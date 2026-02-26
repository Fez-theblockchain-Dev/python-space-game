"""
Unit tests for the Stripe payment handler.

Covers the full payment lifecycle with mocked Stripe calls and an
in-memory SQLite database:
  - PaymentIntent creation
  - Checkout Session creation
  - Webhook processing (success, failure, idempotency)
  - Player wallet crediting
  - Payment verification
  - Periodic API connection health check
"""
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend_apis.models import (
    Base,
    PackageType,
    PACKAGES,
    Player,
    PlayerWallet,
    Transaction,
    TransactionStatus,
)
from backend_apis.stripe_service import (
    StripePaymentResult,
    StripePaymentService,
    StripeWebhookResult,
)
from backend_apis.stripe_payment_handler import CreditResult, StripePaymentHandler


def _make_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


class _DBTestCase(unittest.TestCase):
    """Base class that provides a fresh in-memory DB for every test."""

    def setUp(self):
        self.engine = _make_engine()
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        self.mock_stripe = MagicMock(spec=StripePaymentService)
        self.handler = StripePaymentHandler(stripe_service=self.mock_stripe)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def _seed_player(self, uuid: str = "player-abc-1234") -> Player:
        player = Player(player_uuid=uuid)
        player.wallet = PlayerWallet()
        self.db.add(player)
        self.db.commit()
        self.db.refresh(player)
        return player


class TestGetOrCreatePlayer(_DBTestCase):

    def test_creates_new_player_with_wallet(self):
        player = self.handler.get_or_create_player(self.db, "new-uuid")
        self.assertIsNotNone(player.id)
        self.assertEqual(player.player_uuid, "new-uuid")
        self.assertIsNotNone(player.wallet)

    def test_returns_existing_player(self):
        existing = self._seed_player("existing-uuid")
        returned = self.handler.get_or_create_player(self.db, "existing-uuid")
        self.assertEqual(returned.id, existing.id)


class TestInitiatePurchasePaymentIntent(_DBTestCase):

    def test_success(self):
        self.mock_stripe.create_payment_intent.return_value = StripePaymentResult(
            success=True,
            payment_intent_id="pi_test_123",
            client_secret="pi_test_123_secret",
            merchant_reference="ref_001",
        )

        result = self.handler.initiate_purchase_payment_intent(
            self.db, "player-1", PackageType.STARTER
        )

        self.assertTrue(result.success)
        self.assertEqual(result.payment_intent_id, "pi_test_123")

        txn = self.db.query(Transaction).filter_by(merchant_reference="ref_001").first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.status, TransactionStatus.PENDING)
        self.assertEqual(txn.amount_cents, int(PACKAGES[PackageType.STARTER]["price"] * 100))

    def test_invalid_package_returns_error(self):
        result = self.handler.initiate_purchase_payment_intent(
            self.db, "player-1", "nonexistent_package"
        )
        self.assertFalse(result.success)
        self.assertIn("Invalid package", result.error)

    def test_stripe_failure_propagates(self):
        self.mock_stripe.create_payment_intent.return_value = StripePaymentResult(
            success=False, error="Stripe is down"
        )

        result = self.handler.initiate_purchase_payment_intent(
            self.db, "player-1", PackageType.VALUE
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, "Stripe is down")
        self.assertEqual(self.db.query(Transaction).count(), 0)


class TestInitiatePurchaseCheckout(_DBTestCase):

    def test_success(self):
        self.mock_stripe.create_checkout_session.return_value = StripePaymentResult(
            success=True,
            payment_intent_id=None,
            checkout_url="https://checkout.stripe.com/session_xyz",
            merchant_reference="ref_002",
        )

        result = self.handler.initiate_purchase_checkout(
            self.db, "player-2", PackageType.PREMIUM
        )

        self.assertTrue(result.success)
        self.assertEqual(result.checkout_url, "https://checkout.stripe.com/session_xyz")

        txn = self.db.query(Transaction).filter_by(merchant_reference="ref_002").first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.gold_coins_reward, PACKAGES[PackageType.PREMIUM]["gold_coins"])


class TestProcessWebhookNotification(_DBTestCase):

    def _create_pending_transaction(self, merchant_ref="ref_100", psp_ref="pi_100"):
        player = self._seed_player()
        txn = Transaction(
            player_id=player.id,
            merchant_reference=merchant_ref,
            psp_reference=psp_ref,
            package_type=PackageType.STARTER.value,
            amount_cents=199,
            currency="USD",
            status=TransactionStatus.PENDING,
            gold_coins_reward=100,
            health_packs_reward=1,
        )
        self.db.add(txn)
        self.db.commit()
        return txn

    def test_successful_payment_credits_wallet(self):
        txn = self._create_pending_transaction()

        self.mock_stripe.process_webhook.return_value = StripeWebhookResult(
            valid=True,
            event_type="payment_intent.succeeded",
            payment_intent_id="pi_100",
            merchant_reference="ref_100",
            success=True,
            payment_method_type="card",
            raw_data={"id": "pi_100"},
        )
        self.mock_stripe.get_transaction_status_from_event.return_value = TransactionStatus.CAPTURED
        self.mock_stripe.should_credit_player.return_value = True

        ok, msg = self.handler.process_webhook_notification(
            self.db, b'{"fake": "payload"}', "sig_test"
        )

        self.assertTrue(ok)
        self.db.refresh(txn)
        self.assertEqual(txn.status, TransactionStatus.CAPTURED)

        wallet = txn.player.wallet
        self.assertEqual(wallet.gold_coins, 100)
        self.assertEqual(wallet.health_packs, 1)

    def test_idempotency_prevents_double_credit(self):
        txn = self._create_pending_transaction()
        txn.status = TransactionStatus.CAPTURED
        self.db.commit()

        self.mock_stripe.process_webhook.return_value = StripeWebhookResult(
            valid=True,
            event_type="payment_intent.succeeded",
            payment_intent_id="pi_100",
            merchant_reference="ref_100",
            success=True,
            raw_data={"id": "pi_100"},
        )
        self.mock_stripe.get_transaction_status_from_event.return_value = TransactionStatus.CAPTURED
        self.mock_stripe.should_credit_player.return_value = True

        ok, msg = self.handler.process_webhook_notification(
            self.db, b"payload", "sig"
        )

        self.assertTrue(ok)
        self.assertIn("Already processed", msg)
        wallet = txn.player.wallet
        self.assertEqual(wallet.gold_coins, 0)

    def test_failed_payment_sets_error(self):
        txn = self._create_pending_transaction()

        self.mock_stripe.process_webhook.return_value = StripeWebhookResult(
            valid=True,
            event_type="payment_intent.payment_failed",
            payment_intent_id="pi_100",
            merchant_reference="ref_100",
            success=False,
            raw_data={"id": "pi_100"},
        )
        self.mock_stripe.get_transaction_status_from_event.return_value = TransactionStatus.FAILED
        self.mock_stripe.should_credit_player.return_value = False

        ok, _ = self.handler.process_webhook_notification(
            self.db, b"payload", "sig"
        )

        self.assertTrue(ok)
        self.db.refresh(txn)
        self.assertEqual(txn.status, TransactionStatus.FAILED)
        self.assertIn("Payment failed", txn.error_message)

    def test_invalid_signature_returns_error(self):
        self.mock_stripe.process_webhook.return_value = StripeWebhookResult(
            valid=False, error="Signature verification failed"
        )

        ok, msg = self.handler.process_webhook_notification(
            self.db, b"bad", "bad_sig"
        )

        self.assertFalse(ok)
        self.assertIn("Signature verification failed", msg)

    def test_unknown_merchant_ref_is_non_fatal(self):
        self.mock_stripe.process_webhook.return_value = StripeWebhookResult(
            valid=True,
            event_type="payment_intent.succeeded",
            merchant_reference="unknown_ref",
            success=True,
            raw_data={},
        )
        self.mock_stripe.get_transaction_status_from_event.return_value = TransactionStatus.CAPTURED
        self.mock_stripe.should_credit_player.return_value = True

        ok, msg = self.handler.process_webhook_notification(
            self.db, b"payload", "sig"
        )

        self.assertTrue(ok)
        self.assertIn("Transaction not found", msg)


class TestVerifyPaymentResult(_DBTestCase):

    def test_already_captured_returns_balance(self):
        player = self._seed_player()
        player.wallet.gold_coins = 500
        txn = Transaction(
            player_id=player.id,
            merchant_reference="ref_200",
            psp_reference="pi_200",
            package_type=PackageType.VALUE.value,
            amount_cents=499,
            currency="USD",
            status=TransactionStatus.CAPTURED,
            gold_coins_reward=500,
            health_packs_reward=6,
        )
        self.db.add(txn)
        self.db.commit()

        result = self.handler.verify_payment_result(
            self.db, merchant_reference="ref_200"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.gold_coins_added, 500)

    def test_pending_checks_stripe_and_credits(self):
        player = self._seed_player()
        txn = Transaction(
            player_id=player.id,
            merchant_reference="ref_300",
            psp_reference="pi_300",
            package_type=PackageType.STARTER.value,
            amount_cents=199,
            currency="USD",
            status=TransactionStatus.PENDING,
            gold_coins_reward=100,
            health_packs_reward=1,
        )
        self.db.add(txn)
        self.db.commit()

        self.mock_stripe.retrieve_payment_intent.return_value = {
            "id": "pi_300",
            "status": "succeeded",
            "amount": 199,
            "currency": "usd",
            "metadata": {},
            "payment_method_types": ["card"],
        }

        result = self.handler.verify_payment_result(
            self.db, merchant_reference="ref_300"
        )

        self.assertTrue(result.success)
        self.db.refresh(txn)
        self.assertEqual(txn.status, TransactionStatus.CAPTURED)
        self.assertEqual(player.wallet.gold_coins, 100)

    def test_no_reference_returns_error(self):
        result = self.handler.verify_payment_result(self.db)
        self.assertFalse(result.success)
        self.assertIn("No reference", result.error)


class TestGetAvailablePackages(_DBTestCase):

    def test_returns_all_packages(self):
        packages = self.handler.get_available_packages()
        self.assertEqual(len(packages), len(PACKAGES))
        ids = {p["id"] for p in packages}
        self.assertIn("gold_100", ids)
        self.assertIn("gold_500", ids)
        self.assertIn("gold_1200", ids)


class TestPeriodicAPIConnectionCheck(unittest.TestCase):
    """
    Simulates a periodic health check that verifies the Stripe API
    is reachable by attempting to retrieve a non-existent PaymentIntent.
    A real scheduler (e.g. APScheduler, cron) would call this at an interval.
    """

    @patch("stripe.PaymentIntent.retrieve")
    def test_api_reachable(self, mock_retrieve):
        mock_retrieve.return_value = MagicMock(
            id="pi_health", status="succeeded"
        )

        service = StripePaymentService.__new__(StripePaymentService)
        service.api_key = "sk_test_fake"
        service.publishable_key = "pk_test_fake"
        service.webhook_secret = "whsec_fake"
        service.return_url = "http://localhost"

        result = service.retrieve_payment_intent("pi_health")

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "succeeded")
        mock_retrieve.assert_called_once_with("pi_health")

    @patch("stripe.PaymentIntent.retrieve")
    def test_api_unreachable(self, mock_retrieve):
        import stripe as stripe_mod
        mock_retrieve.side_effect = stripe_mod.StripeError("Connection error")

        service = StripePaymentService.__new__(StripePaymentService)
        service.api_key = "sk_test_fake"
        service.publishable_key = "pk_test_fake"
        service.webhook_secret = "whsec_fake"
        service.return_url = "http://localhost"

        result = service.retrieve_payment_intent("pi_health")

        self.assertIsNone(result)

    @patch("stripe.PaymentIntent.retrieve")
    def test_periodic_check_multiple_intervals(self, mock_retrieve):
        """Simulates N consecutive health-check polls."""
        mock_retrieve.return_value = MagicMock(
            id="pi_health", status="requires_payment_method"
        )

        service = StripePaymentService.__new__(StripePaymentService)
        service.api_key = "sk_test_fake"
        service.publishable_key = "pk_test_fake"
        service.webhook_secret = "whsec_fake"
        service.return_url = "http://localhost"

        num_checks = 5
        results = [service.retrieve_payment_intent("pi_health") for _ in range(num_checks)]

        self.assertTrue(all(r is not None for r in results))
        self.assertEqual(mock_retrieve.call_count, num_checks)


if __name__ == "__main__":
    unittest.main()
