"""
Payment Handler - Orchestrates payment flow between Adyen and database.
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
from .adyen_service import (
    AdyenPaymentService, 
    PaymentSessionResult, 
    WebhookVerificationResult
)


@dataclass
class CreditResult:
    """Result from crediting a player's account."""
    success: bool
    gold_coins_added: int = 0
    health_packs_added: int = 0
    new_balance: Optional[dict] = None
    error: Optional[str] = None


class PaymentHandler:
    """
    Handles the complete payment flow:
    - Creating payment sessions with database tracking
    - Processing webhooks and crediting accounts
    - Managing player wallets
    """
    
    def __init__(self, adyen_service: AdyenPaymentService):
        self.adyen = adyen_service
    
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
    
    def initiate_purchase(
        self,
        db: Session,
        player_uuid: str,
        package_type: PackageType,
        use_payment_link: bool = False,
        shopper_email: Optional[str] = None,
    ) -> PaymentSessionResult:
        """
        Initiate a purchase by creating an Adyen session and database transaction.
        
        Args:
            db: Database session
            player_uuid: Player's unique identifier
            package_type: Type of package to purchase
            use_payment_link: Use payment link instead of checkout session
            shopper_email: Optional email for receipt
            
        Returns:
            PaymentSessionResult with checkout details
        """
        # Validate package
        if package_type not in PACKAGES:
            return PaymentSessionResult(
                success=False,
                error=f"Invalid package: {package_type}"
            )
        
        package = PACKAGES[package_type]
        
        # Ensure player exists
        player = self.get_or_create_player(db, player_uuid)
        
        # Create Adyen session
        if use_payment_link:
            result = self.adyen.create_payment_link(
                player_uuid=player_uuid,
                package_type=package_type,
                shopper_email=shopper_email,
            )
        else:
            result = self.adyen.create_checkout_session(
                player_uuid=player_uuid,
                package_type=package_type,
                shopper_email=shopper_email,
            )
        
        if not result.success:
            return result
        
        # Create transaction record
        transaction = Transaction(
            player_id=player.id,
            merchant_reference=result.merchant_reference,
            session_id=result.session_id,
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
        payload: dict,
    ) -> tuple[bool, str]:
        """
        Process an Adyen webhook notification.
        
        Args:
            db: Database session
            payload: Webhook JSON payload
            
        Returns:
            Tuple of (success, message)
        """
        # Verify and parse webhook
        webhook_result = self.adyen.process_webhook(payload)
        
        if not webhook_result.valid:
            return False, webhook_result.error or "Invalid webhook"
        
        merchant_reference = webhook_result.merchant_reference
        
        if not merchant_reference:
            return False, "Missing merchant reference in webhook"
        
        # Find the transaction
        transaction = db.query(Transaction).filter(
            Transaction.merchant_reference == merchant_reference
        ).first()
        
        if not transaction:
            # Transaction not found - might be from a different system
            # Still acknowledge to prevent retry
            return True, f"Transaction not found: {merchant_reference}"
        
        # Update transaction with webhook data
        transaction.psp_reference = webhook_result.psp_reference
        transaction.payment_method = webhook_result.payment_method
        transaction.webhook_data = json.dumps(webhook_result.raw_data)
        transaction.updated_at = datetime.utcnow()
        
        # Map event to status
        new_status = self.adyen.get_transaction_status_from_event(
            webhook_result.event_code,
            webhook_result.success
        )
        transaction.status = new_status
        
        # Check if we should credit the player
        if self.adyen.should_credit_player(webhook_result.event_code, webhook_result.success):
            credit_result = self._credit_player_for_transaction(db, transaction)
            
            if credit_result.success:
                transaction.completed_at = datetime.utcnow()
            else:
                transaction.error_message = credit_result.error
        
        # Handle failed payments
        if new_status == TransactionStatus.FAILED:
            transaction.error_message = f"Payment failed: {webhook_result.event_code}"
        
        db.commit()
        
        return True, f"Processed {webhook_result.event_code} for {merchant_reference}"
    
    def _credit_player_for_transaction(
        self,
        db: Session,
        transaction: Transaction,
    ) -> CreditResult:
        """
        Credit a player's wallet for a completed transaction.
        
        Args:
            db: Database session
            transaction: The transaction to credit
            
        Returns:
            CreditResult with details of the credit
        """
        # Get the player and wallet
        player = transaction.player
        
        if not player:
            return CreditResult(
                success=False,
                error="Player not found for transaction"
            )
        
        wallet = player.wallet
        
        if not wallet:
            # Create wallet if missing
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
    
    def verify_and_credit_redirect(
        self,
        db: Session,
        merchant_reference: str,
        redirect_result: Optional[str] = None,
    ) -> CreditResult:
        """
        Verify payment after redirect (for Drop-in/Components integration).
        This is a fallback - primary crediting should happen via webhooks.
        
        Args:
            db: Database session
            merchant_reference: The merchant reference from URL params
            redirect_result: Optional redirectResult from Adyen
            
        Returns:
            CreditResult (may just confirm pending status)
        """
        transaction = db.query(Transaction).filter(
            Transaction.merchant_reference == merchant_reference
        ).first()
        
        if not transaction:
            return CreditResult(
                success=False,
                error=f"Transaction not found: {merchant_reference}"
            )
        
        # If already completed, return current balance
        if transaction.status == TransactionStatus.CAPTURED:
            return CreditResult(
                success=True,
                gold_coins_added=transaction.gold_coins_reward,
                health_packs_added=transaction.health_packs_reward,
                new_balance=transaction.player.wallet.to_dict() if transaction.player.wallet else None,
            )
        
        # If still pending, inform that webhook will handle it
        if transaction.status == TransactionStatus.PENDING:
            return CreditResult(
                success=True,
                error="Payment is being processed. Credits will be added shortly."
            )
        
        # If authorized (webhook already processed), return success
        if transaction.status == TransactionStatus.AUTHORIZED:
            return CreditResult(
                success=True,
                gold_coins_added=transaction.gold_coins_reward,
                health_packs_added=transaction.health_packs_reward,
                new_balance=transaction.player.wallet.to_dict() if transaction.player.wallet else None,
            )
        
        return CreditResult(
            success=False,
            error=f"Transaction status: {transaction.status.value}"
        )
    
    def get_transaction_history(
        self,
        db: Session,
        player_uuid: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        Get transaction history for a player.
        
        Args:
            db: Database session
            player_uuid: Player's unique identifier
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction dictionaries
        """
        player = db.query(Player).filter(Player.player_uuid == player_uuid).first()
        
        if not player:
            return []
        
        transactions = db.query(Transaction).filter(
            Transaction.player_id == player.id
        ).order_by(
            Transaction.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "reference": t.merchant_reference,
                "package": t.package_type,
                "amount_usd": t.amount_cents / 100.0,
                "status": t.status.value,
                "gold_coins": t.gold_coins_reward,
                "health_packs": t.health_packs_reward,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in transactions
        ]
    
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

