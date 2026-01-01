"""
Adyen Payment Service for handling checkout sessions and payment verification.

Documentation: https://docs.adyen.com/api-explorer/Checkout/71/overview
"""
import os
import hmac
import hashlib
import base64
import json
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

# Adyen Python SDK
# pip install Adyen
import Adyen

from .models import PackageType, PACKAGES, TransactionStatus


@dataclass
class PaymentSessionResult:
    """Result from creating a payment session."""
    success: bool
    session_id: Optional[str] = None
    session_data: Optional[str] = None
    checkout_url: Optional[str] = None
    merchant_reference: Optional[str] = None
    error: Optional[str] = None


@dataclass
class WebhookVerificationResult:
    """Result from verifying a webhook."""
    valid: bool
    event_code: Optional[str] = None
    psp_reference: Optional[str] = None
    merchant_reference: Optional[str] = None
    success: Optional[bool] = None
    payment_method: Optional[str] = None
    raw_data: Optional[dict] = None
    error: Optional[str] = None


class AdyenPaymentService:
    """
    Handles Adyen payment operations including:
    - Creating checkout sessions
    - Verifying webhooks
    - Processing payment results
    """
    
    def __init__(
        self,
        api_key: str = None,
        merchant_account: str = None,
        environment: str = "test",
        hmac_key: str = None,
        return_url: str = None,
    ):
        """
        Initialize the Adyen payment service.
        
        Args:
            api_key: Adyen API key (from Customer Area)
            merchant_account: Your Adyen merchant account name
            environment: 'test' or 'live'
            hmac_key: HMAC key for webhook verification (from Customer Area)
            return_url: URL to redirect after payment
        """
        self.api_key = api_key or os.getenv("ADYEN_API_KEY")
        self.merchant_account = merchant_account or os.getenv("ADYEN_MERCHANT_ACCOUNT")
        self.environment = environment or os.getenv("ADYEN_ENVIRONMENT", "test")
        self.hmac_key = hmac_key or os.getenv("ADYEN_HMAC_KEY")
        self.return_url = return_url or os.getenv("ADYEN_RETURN_URL", "http://localhost:8000/payment/result")
        
        # Initialize Adyen client
        self.adyen = Adyen.Adyen()
        self.adyen.payment.client.xapikey = self.api_key
        self.adyen.payment.client.platform = self.environment
    
    def generate_merchant_reference(self, player_uuid: str, package_type: PackageType) -> str:
        """Generate a unique merchant reference for the transaction."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{player_uuid[:8]}_{package_type.value}_{timestamp}_{unique_id}"
    
    def create_checkout_session(
        self,
        player_uuid: str,
        package_type: PackageType,
        country_code: str = "US",
        shopper_locale: str = "en-US",
        shopper_email: Optional[str] = None,
    ) -> PaymentSessionResult:
        """
        Create an Adyen checkout session for a package purchase.
        
        Args:
            player_uuid: The player's unique identifier
            package_type: The type of package being purchased
            country_code: 2-letter country code
            shopper_locale: Locale for the checkout page
            shopper_email: Optional email for receipt
            
        Returns:
            PaymentSessionResult with session details or error
        """
        if package_type not in PACKAGES:
            return PaymentSessionResult(
                success=False,
                error=f"Invalid package type: {package_type}"
            )
        
        package = PACKAGES[package_type]
        amount_cents = int(package["price"] * 100)
        merchant_reference = self.generate_merchant_reference(player_uuid, package_type)
        
        request_data = {
            "merchantAccount": self.merchant_account,
            "amount": {
                "value": amount_cents,
                "currency": "USD"
            },
            "reference": merchant_reference,
            "returnUrl": f"{self.return_url}?ref={merchant_reference}",
            "countryCode": country_code,
            "shopperLocale": shopper_locale,
            "shopperReference": player_uuid,
            "channel": "Web",
            "lineItems": [
                {
                    "id": package_type.value,
                    "description": package["name"],
                    "amountIncludingTax": amount_cents,
                    "quantity": 1,
                }
            ],
            "metadata": {
                "player_uuid": player_uuid,
                "package_type": package_type.value,
                "gold_coins": str(package["gold_coins"]),
                "health_packs": str(package["health_packs"]),
            }
        }
        
        if shopper_email:
            request_data["shopperEmail"] = shopper_email
        
        try:
            result = self.adyen.checkout.sessions_api.sessions(request_data)
            
            if result.status_code == 201:
                response_data = result.message
                return PaymentSessionResult(
                    success=True,
                    session_id=response_data.get("id"),
                    session_data=response_data.get("sessionData"),
                    checkout_url=response_data.get("url"),  # For redirect integration
                    merchant_reference=merchant_reference,
                )
            else:
                return PaymentSessionResult(
                    success=False,
                    error=f"Adyen API error: {result.status_code} - {result.message}"
                )
                
        except Exception as e:
            return PaymentSessionResult(
                success=False,
                error=f"Failed to create checkout session: {str(e)}"
            )
    
    def create_payment_link(
        self,
        player_uuid: str,
        package_type: PackageType,
        expires_in_days: int = 1,
        shopper_email: Optional[str] = None,
    ) -> PaymentSessionResult:
        """
        Create a shareable payment link (alternative to checkout session).
        Good for email/SMS payment links.
        
        Args:
            player_uuid: The player's unique identifier
            package_type: The type of package being purchased
            expires_in_days: Days until the link expires
            shopper_email: Optional email for receipt
            
        Returns:
            PaymentSessionResult with payment link or error
        """
        if package_type not in PACKAGES:
            return PaymentSessionResult(
                success=False,
                error=f"Invalid package type: {package_type}"
            )
        
        package = PACKAGES[package_type]
        amount_cents = int(package["price"] * 100)
        merchant_reference = self.generate_merchant_reference(player_uuid, package_type)
        
        # Calculate expiry date
        from datetime import timedelta
        expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat() + "Z"
        
        request_data = {
            "merchantAccount": self.merchant_account,
            "amount": {
                "value": amount_cents,
                "currency": "USD"
            },
            "reference": merchant_reference,
            "returnUrl": f"{self.return_url}?ref={merchant_reference}",
            "shopperReference": player_uuid,
            "expiresAt": expires_at,
            "reusable": False,
            "metadata": {
                "player_uuid": player_uuid,
                "package_type": package_type.value,
                "gold_coins": str(package["gold_coins"]),
                "health_packs": str(package["health_packs"]),
            }
        }
        
        if shopper_email:
            request_data["shopperEmail"] = shopper_email
        
        try:
            result = self.adyen.checkout.payment_links_api.payment_links(request_data)
            
            if result.status_code in [200, 201]:
                response_data = result.message
                return PaymentSessionResult(
                    success=True,
                    session_id=response_data.get("id"),
                    checkout_url=response_data.get("url"),
                    merchant_reference=merchant_reference,
                )
            else:
                return PaymentSessionResult(
                    success=False,
                    error=f"Adyen API error: {result.status_code} - {result.message}"
                )
                
        except Exception as e:
            return PaymentSessionResult(
                success=False,
                error=f"Failed to create payment link: {str(e)}"
            )
    
    def verify_webhook_hmac(self, notification_item: dict) -> bool:
        """
        Verify the HMAC signature of an Adyen webhook notification.
        
        Args:
            notification_item: The notification item from the webhook payload
            
        Returns:
            True if the signature is valid
        """
        if not self.hmac_key:
            # If no HMAC key configured, skip verification (not recommended for production)
            return True
        
        try:
            # Get the HMAC signature from the notification
            additional_data = notification_item.get("additionalData", {})
            received_hmac = additional_data.get("hmacSignature")
            
            if not received_hmac:
                return False
            
            # Build the signing string
            # Order matters! Follow Adyen's specification
            signing_parts = [
                notification_item.get("pspReference", ""),
                notification_item.get("originalReference", ""),
                notification_item.get("merchantAccountCode", ""),
                notification_item.get("merchantReference", ""),
                str(notification_item.get("amount", {}).get("value", "")),
                notification_item.get("amount", {}).get("currency", ""),
                notification_item.get("eventCode", ""),
                notification_item.get("success", ""),
            ]
            signing_string = ":".join(signing_parts)
            
            # Calculate expected HMAC
            hmac_key_bytes = bytes.fromhex(self.hmac_key)
            calculated_hmac = hmac.new(
                hmac_key_bytes,
                signing_string.encode("utf-8"),
                hashlib.sha256
            )
            expected_hmac = base64.b64encode(calculated_hmac.digest()).decode("utf-8")
            
            return hmac.compare_digest(received_hmac, expected_hmac)
            
        except Exception:
            return False
    
    def process_webhook(self, payload: dict) -> WebhookVerificationResult:
        """
        Process an Adyen webhook notification.
        
        Args:
            payload: The full webhook JSON payload
            
        Returns:
            WebhookVerificationResult with parsed notification data
        """
        try:
            notification_items = payload.get("notificationItems", [])
            
            if not notification_items:
                return WebhookVerificationResult(
                    valid=False,
                    error="No notification items in payload"
                )
            
            # Process the first notification item
            # In production, you might want to process all items
            notification_item = notification_items[0].get("NotificationRequestItem", {})
            
            # Verify HMAC signature
            if not self.verify_webhook_hmac(notification_item):
                return WebhookVerificationResult(
                    valid=False,
                    error="HMAC signature verification failed"
                )
            
            event_code = notification_item.get("eventCode")
            success = notification_item.get("success") == "true"
            
            return WebhookVerificationResult(
                valid=True,
                event_code=event_code,
                psp_reference=notification_item.get("pspReference"),
                merchant_reference=notification_item.get("merchantReference"),
                success=success,
                payment_method=notification_item.get("paymentMethod"),
                raw_data=notification_item,
            )
            
        except Exception as e:
            return WebhookVerificationResult(
                valid=False,
                error=f"Failed to process webhook: {str(e)}"
            )
    
    def get_transaction_status_from_event(self, event_code: str, success: bool) -> TransactionStatus:
        """
        Map Adyen event codes to internal transaction status.
        
        Args:
            event_code: Adyen event code (e.g., AUTHORISATION, CAPTURE)
            success: Whether the event was successful
            
        Returns:
            TransactionStatus enum value
        """
        if not success:
            return TransactionStatus.FAILED
        
        status_map = {
            "AUTHORISATION": TransactionStatus.AUTHORIZED,
            "CAPTURE": TransactionStatus.CAPTURED,
            "CANCELLATION": TransactionStatus.CANCELLED,
            "REFUND": TransactionStatus.REFUNDED,
        }
        
        return status_map.get(event_code, TransactionStatus.PENDING)
    
    def should_credit_player(self, event_code: str, success: bool) -> bool:
        """
        Determine if the player should be credited based on the event.
        
        For most integrations, credit on AUTHORISATION.
        For manual capture flows, credit on CAPTURE.
        
        Args:
            event_code: Adyen event code
            success: Whether the event was successful
            
        Returns:
            True if player should be credited
        """
        # Credit on successful authorization (immediate capture)
        # Adjust this based on your capture settings
        return event_code == "AUTHORISATION" and success

