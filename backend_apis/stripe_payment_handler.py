"""
Stripe Payment Handler - Orchestrates payment flow between Stripe and database.
"""
import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

from .models import (
    Player, PlayerWallet, Transaction, 
    PackageType, PACKAGES, TransactionStatus
)
from .stripe_service import (
    StripePaymentService, 
    StripePaymentResult, 
    StripeWebhookResult
)


@dataclass
class CreditResult:
    """Result from crediting a player's account."""
    success: bool
    gold_coins_added: int = 0
    health_packs_added: int = 0
    new_balance: Optional[dict] = None
    error: Optional[str] = None


class StripePaymentHandler:
    """
    Handles the complete Stripe payment flow:
    - Creating payment intents and checkout sessions with database tracking
    - Processing webhooks and crediting accounts
    - Managing player wallets
    """
    
    def __init__(self, stripe_service: StripePaymentService):
        self.stripe = stripe_service
    
    def get_or_create_player(self, db: Session, player_uuid: str) -> Player:
        """Get existing player or create a new one with wallet."""
        player = db.query(Player).filter(Player.player_uuid == player_uuid).first()
        
        if not player:
            player = Player(player_uuid=player_uuid)
            player.wallet = PlayerWallet()
            db.add(player)
            db.commit()
            db.refresh(player)
        
        return player
    
    def get_player_wallet(self, db: Session, player_uuid: str) -> Optional[dict]:
        """Get player's wallet balance."""
        player = db.query(Player).filter(Player.player_uuid == player_uuid).first()
        
        if not player or not player.wallet:
            return None
        
        return player.wallet.to_dict()
    
    def initiate_purchase_payment_intent(
        self,
        db: Session,
        player_uuid: str,
        package_type: PackageType,
        customer_email: Optional[str] = None,
    ) -> StripePaymentResult:
        """
        Initiate a purchase by creating a Stripe PaymentIntent.
        
        This is used with the Express Checkout Element for Apple Pay.
        
        Args:
            db: Database session
            player_uuid: Player's unique identifier
            package_type: Type of package to purchase
            customer_email: Optional email for receipt
            
        Returns:
            StripePaymentResult with PaymentIntent details
        """
        # Validate package
        if package_type not in PACKAGES:
            return StripePaymentResult(
                success=False,
                error=f"Invalid package: {package_type}"
            )
        
        package = PACKAGES[package_type]
        
        # Ensure player exists
        player = self.get_or_create_player(db, player_uuid)
        
        # Create Stripe PaymentIntent
        result = self.stripe.create_payment_intent(
            player_uuid=player_uuid,
            package_type=package_type,
            customer_email=customer_email,
        )
        
        if not result.success:
            return result
        
        # Create transaction record
        transaction = Transaction(
            player_id=player.id,
            merchant_reference=result.merchant_reference,
            psp_reference=result.payment_intent_id,  # Store PaymentIntent ID
            package_type=package_type.value,
            amount_cents=int(package["price"] * 100),
            currency="USD",
            status=TransactionStatus.PENDING,
            gold_coins_reward=package["gold_coins"],
            health_packs_reward=package["health_packs"],
        )
        
        db.add(transaction)
        db.commit()
        
        return result
    
    def initiate_purchase_checkout(
        self,
        db: Session,
        player_uuid: str,
        package_type: PackageType,
        success_url: str = None,
        cancel_url: str = None,
        customer_email: Optional[str] = None,
    ) -> StripePaymentResult:
        """
        Initiate a purchase using Stripe Checkout (hosted page).
        
        Args:
            db: Database session
            player_uuid: Player's unique identifier
            package_type: Type of package to purchase
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            customer_email: Optional email for receipt
            
        Returns:
            StripePaymentResult with checkout details
        """
        # Validate package
        if package_type not in PACKAGES:
            return StripePaymentResult(
                success=False,
                error=f"Invalid package: {package_type}"
            )
        
        package = PACKAGES[package_type]
        
        # Ensure player exists
        player = self.get_or_create_player(db, player_uuid)
        
        # Create Stripe Checkout Session
        result = self.stripe.create_checkout_session(
            player_uuid=player_uuid,
            package_type=package_type,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email,
        )
        
        if not result.success:
            return result
        
        # Create transaction record
        transaction = Transaction(
            player_id=player.id,
            merchant_reference=result.merchant_reference,
            psp_reference=result.payment_intent_id,
            package_type=package_type.value,
            amount_cents=int(package["price"] * 100),
            currency="USD",
            status=TransactionStatus.PENDING,
            gold_coins_reward=package["gold_coins"],
            health_packs_reward=package["health_packs"],
        )
        
        db.add(transaction)
        db.commit()
        
        return result
    
    def process_webhook_notification(
        self,
        db: Session,
        payload: bytes,
        signature: str,
    ) -> tuple[bool, str]:
        """
        Process a Stripe webhook notification.
        
        Args:
            db: Database session
            payload: Raw request body
            signature: Stripe-Signature header
            
        Returns:
            Tuple of (success, message)
        """
        # Verify and parse webhook
        webhook_result = self.stripe.process_webhook(payload, signature)
        
        if not webhook_result.valid:
            return False, webhook_result.error or "Invalid webhook"
        
        merchant_reference = webhook_result.merchant_reference
        
        if not merchant_reference:
            # Try to get from payment intent if not in metadata
            if webhook_result.payment_intent_id:
                transaction = db.query(Transaction).filter(
                    Transaction.psp_reference == webhook_result.payment_intent_id
                ).first()
                if transaction:
                    merchant_reference = transaction.merchant_reference
        
        if not merchant_reference:
            return True, f"No merchant reference for event: {webhook_result.event_type}"
        
        # Find the transaction
        transaction = db.query(Transaction).filter(
            Transaction.merchant_reference == merchant_reference
        ).first()
        
        if not transaction:
            return True, f"Transaction not found: {merchant_reference}"
        
        # Update transaction with webhook data
        transaction.psp_reference = webhook_result.payment_intent_id or transaction.psp_reference
        transaction.payment_method = webhook_result.payment_method_type
        transaction.webhook_data = json.dumps(webhook_result.raw_data)
        transaction.updated_at = datetime.utcnow()
        
        # Map event to status
        new_status = self.stripe.get_transaction_status_from_event(
            webhook_result.event_type,
            webhook_result.success or False
        )
        transaction.status = new_status
        
        # Check if we should credit the player
        if self.stripe.should_credit_player(webhook_result.event_type, webhook_result.success or False):
            credit_result = self._credit_player_for_transaction(db, transaction)
            
            if credit_result.success:
                transaction.completed_at = datetime.utcnow()
            else:
                transaction.error_message = credit_result.error
        
        # Handle failed payments
        if new_status == TransactionStatus.FAILED:
            transaction.error_message = f"Payment failed: {webhook_result.event_type}"
        
        db.commit()
        
        return True, f"Processed {webhook_result.event_type} for {merchant_reference}"
    
    def _credit_player_for_transaction(
        self,
        db: Session,
        transaction: Transaction,
    ) -> CreditResult:
        """
        Credit a player's wallet for a completed transaction.
        """
        player = transaction.player
        
        if not player:
            return CreditResult(
                success=False,
                error="Player not found for transaction"
            )
        
        wallet = player.wallet
        
        if not wallet:
            wallet = PlayerWallet(player_id=player.id)
            db.add(wallet)
        
        # Add rewards
        gold_to_add = transaction.gold_coins_reward
        health_to_add = transaction.health_packs_reward
        
        wallet.add_gold_coins(gold_to_add)
        wallet.add_health_packs(health_to_add)
        wallet.total_spent_usd += transaction.amount_cents / 100.0
        
        db.commit()
        
        return CreditResult(
            success=True,
            gold_coins_added=gold_to_add,
            health_packs_added=health_to_add,
            new_balance=wallet.to_dict(),
        )
    
    def verify_payment_result(
        self,
        db: Session,
        merchant_reference: str = None,
        payment_intent_id: str = None,
    ) -> CreditResult:
        """
        Verify payment after redirect or confirmation.
        
        Args:
            db: Database session
            merchant_reference: The merchant reference from URL params
            payment_intent_id: Optional PaymentIntent ID
            
        Returns:
            CreditResult with status
        """
        # Find transaction
        if merchant_reference:
            transaction = db.query(Transaction).filter(
                Transaction.merchant_reference == merchant_reference
            ).first()
        elif payment_intent_id:
            transaction = db.query(Transaction).filter(
                Transaction.psp_reference == payment_intent_id
            ).first()
        else:
            return CreditResult(success=False, error="No reference provided")
        
        if not transaction:
            return CreditResult(
                success=False,
                error="Transaction not found"
            )
        
        # If already completed, return success
        if transaction.status == TransactionStatus.CAPTURED:
            return CreditResult(
                success=True,
                gold_coins_added=transaction.gold_coins_reward,
                health_packs_added=transaction.health_packs_reward,
                new_balance=transaction.player.wallet.to_dict() if transaction.player.wallet else None,
            )
        
        # If pending, check with Stripe
        if transaction.status == TransactionStatus.PENDING and transaction.psp_reference:
            intent_data = self.stripe.retrieve_payment_intent(transaction.psp_reference)
            
            if intent_data and intent_data["status"] == "succeeded":
                # Credit the player
                credit_result = self._credit_player_for_transaction(db, transaction)
                transaction.status = TransactionStatus.CAPTURED
                transaction.completed_at = datetime.utcnow()
                db.commit()
                return credit_result
        
        # Still processing
        return CreditResult(
            success=True,
            error="Payment is being processed. Credits will be added shortly."
        )
    
    def get_available_packages(self) -> list[dict]:
        """Get list of available packages for purchase."""
        return [
            {
                "id": package_type.value,
                "name": package["name"],
                "price_usd": package["price"],
                "gold_coins": package["gold_coins"],
                "health_packs": package["health_packs"],
            }
            for package_type, package in PACKAGES.items()
        ]

