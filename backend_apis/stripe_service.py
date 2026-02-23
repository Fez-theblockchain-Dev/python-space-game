"""
Stripe Payment Service for handling Apple Pay and other payment methods.

Documentation: https://docs.stripe.com/apple-pay?platform=web
"""
import os
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

import stripe

from .models import PackageType, PACKAGES, TransactionStatus


@dataclass
class StripePaymentResult:
    """Result from creating a payment intent or checkout session."""
    success: bool
    payment_intent_id: Optional[str] = None
    client_secret: Optional[str] = None
    checkout_url: Optional[str] = None
    merchant_reference: Optional[str] = None
    publishable_key: Optional[str] = None
    error: Optional[str] = None


@dataclass
class StripeWebhookResult:
    """Result from processing a Stripe webhook."""
    valid: bool
    event_type: Optional[str] = None
    payment_intent_id: Optional[str] = None
    merchant_reference: Optional[str] = None
    success: Optional[bool] = None
    payment_method_type: Optional[str] = None
    raw_data: Optional[dict] = None
    error: Optional[str] = None


class StripePaymentService:
    """
    Handles Stripe payment operations including:
    - Creating Payment Intents for Apple Pay
    - Creating Checkout Sessions
    - Verifying webhooks
    - Processing payment results
    
    Apple Pay Setup:
    1. Register your domain with Stripe (Dashboard > Settings > Payment methods > Apple Pay)
    2. Use the Express Checkout Element on your frontend
    3. Stripe handles Apple merchant validation automatically
    """
    
    def __init__(
        self,
        api_key: str = None,
        publishable_key: str = None,
        webhook_secret: str = None,
        return_url: str = None,
    ):
        """
        Initialize the Stripe payment service.
        
        Args:
            api_key: Stripe secret API key (sk_test_... or sk_live_...)
            publishable_key: Stripe publishable key (pk_test_... or pk_live_...)
            webhook_secret: Webhook endpoint signing secret (whsec_...)
            return_url: URL to redirect after payment
        """
        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = publishable_key or os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = webhook_secret or os.getenv("STRIPE_WEBHOOK_SECRET")
        self.return_url = return_url or os.getenv("STRIPE_RETURN_URL", "http://localhost:8000/payment/result")
        
        # Initialize Stripe with the API key
        stripe.api_key = stripe.StripeClient(api_key)
    
    def generate_merchant_reference(self, player_uuid: str, package_type: PackageType) -> str:
        """Generate a unique merchant reference for the transaction."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{player_uuid[:8]}_{package_type.value}_{timestamp}_{unique_id}"
    
    def create_payment_intent(
        self,
        player_uuid: str,
        package_type: PackageType,
        payment_method_types: list[str] = None,
        customer_email: Optional[str] = None,
    ) -> StripePaymentResult:
        """
        Create a Stripe PaymentIntent for Apple Pay and card payments.
        
        This is the recommended approach for Apple Pay using the Express Checkout Element.
        The client_secret is used to confirm the payment on the frontend.
        
        Args:
            player_uuid: The player's unique identifier
            package_type: The type of package being purchased
            payment_method_types: List of payment methods to accept (default: card, apple_pay)
            customer_email: Optional email for receipt
            
        Returns:
            StripePaymentResult with PaymentIntent details or error
        """
        if package_type not in PACKAGES:
            return StripePaymentResult(
                success=False,
                error=f"Invalid package type: {package_type}"
            )
        
        package = PACKAGES[package_type]
        amount_cents = int(package["price"] * 100)
        merchant_reference = self.generate_merchant_reference(player_uuid, package_type)
        
        # Default to card (which includes Apple Pay via Express Checkout Element)
        if payment_method_types is None:
            automatic_payment_methods={"enabled": True} 
        
        try:
            # Create or retrieve customer
            customer = None
            if customer_email:
                # Search for existing customer
                customers = stripe.Customer.list(email=customer_email, limit=1)
                if customers.data:
                    customer = customers.data[0]
                else:
                    customer = stripe.Customer.create(
                        email=customer_email,
                        metadata={"player_uuid": player_uuid}
                    )
            
            # Build payment intent parameters
            intent_params = {
                "amount": amount_cents,
                "currency": "usd",
                "payment_method_types": payment_method_types,
                "metadata": {
                    "player_uuid": player_uuid,
                    "package_type": package_type.value,
                    "merchant_reference": merchant_reference,
                    "gold_coins": str(package["gold_coins"]),
                    "health_packs": str(package["health_packs"]),
                },
                "description": package["name"],
            }
            
            if customer:
                intent_params["customer"] = customer.id
                intent_params["receipt_email"] = customer_email
            
            payment_intent = stripe.PaymentIntent.create(**intent_params)
            
            return StripePaymentResult(
                success=True,
                payment_intent_id=payment_intent.id,
                client_secret=payment_intent.client_secret,
                merchant_reference=merchant_reference,
                publishable_key=self.publishable_key,
            )
            
        except stripe.error.StripeError as e:
            return StripePaymentResult(
                success=False,
                error=f"Stripe API error: {str(e)}"
            )
        except Exception as e:
            return StripePaymentResult(
                success=False,
                error=f"Failed to create payment intent: {str(e)}"
            )
    
    def create_checkout_session(
        self,
        player_uuid: str,
        package_type: PackageType,
        success_url: str = None,
        cancel_url: str = None,
        customer_email: Optional[str] = None,
    ) -> StripePaymentResult:
        """
        Create a Stripe Checkout Session (hosted payment page).
        
        Apple Pay is automatically enabled in Checkout when configured in Dashboard.
        
        Args:
            player_uuid: The player's unique identifier
            package_type: The type of package being purchased
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            customer_email: Optional email for receipt
            
        Returns:
            StripePaymentResult with checkout session details or error
        """
        if package_type not in PACKAGES:
            return StripePaymentResult(
                success=False,
                error=f"Invalid package type: {package_type}"
            )
        
        package = PACKAGES[package_type]
        amount_cents = int(package["price"] * 100)
        merchant_reference = self.generate_merchant_reference(player_uuid, package_type)
        
        success_url = success_url or f"{self.return_url}?ref={merchant_reference}&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = cancel_url or f"{self.return_url}?ref={merchant_reference}&cancelled=true"
        
        try:
            session_params = {
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "line_items": [
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": package["name"],
                                "description": f"Gold Coins: {package['gold_coins']}, Health Packs: {package['health_packs']}",
                            },
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                "metadata": {
                    "player_uuid": player_uuid,
                    "package_type": package_type.value,
                    "merchant_reference": merchant_reference,
                    "gold_coins": str(package["gold_coins"]),
                    "health_packs": str(package["health_packs"]),
                },
                # Enable automatic payment methods including Apple Pay
                "payment_method_types": ["card"],
            }
            
            if customer_email:
                session_params["customer_email"] = customer_email
            
            session = stripe.checkout.Session.create(**session_params)
            
            return StripePaymentResult(
                success=True,
                payment_intent_id=session.payment_intent,
                checkout_url=session.url,
                merchant_reference=merchant_reference,
            )
            
        except stripe.error.StripeError as e:
            return StripePaymentResult(
                success=False,
                error=f"Stripe API error: {str(e)}"
            )
        except Exception as e:
            return StripePaymentResult(
                success=False,
                error=f"Failed to create checkout session: {str(e)}"
            )
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the Stripe webhook signature.
        
        Args:
            payload: The raw request body
            signature: The Stripe-Signature header value
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            return True  # Skip verification if not configured (not recommended for production)
        
        try:
            stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return True
        except (ValueError, stripe.error.SignatureVerificationError):
            return False
    
    def process_webhook(self, payload: bytes, signature: str) -> StripeWebhookResult:
        """
        Process a Stripe webhook event.
        
        Args:
            payload: The raw request body
            signature: The Stripe-Signature header value
            
        Returns:
            StripeWebhookResult with parsed event data
        """
        try:
            if self.webhook_secret:
                event = stripe.Webhook.construct_event(
                    payload, signature, self.webhook_secret
                )
            else:
                import json
                event = stripe.Event.construct_from(
                    json.loads(payload), stripe.api_key
                )
            
            event_type = event.type
            data_object = event.data.object
            
            # Extract relevant information based on event type
            payment_intent_id = None
            merchant_reference = None
            success = None
            payment_method_type = None
            
            if event_type.startswith("payment_intent."):
                payment_intent_id = data_object.id
                merchant_reference = data_object.metadata.get("merchant_reference")
                payment_method_type = data_object.payment_method_types[0] if data_object.payment_method_types else None
                
                if event_type == "payment_intent.succeeded":
                    success = True
                elif event_type in ["payment_intent.payment_failed", "payment_intent.canceled"]:
                    success = False
            
            elif event_type.startswith("checkout.session."):
                merchant_reference = data_object.metadata.get("merchant_reference")
                payment_intent_id = data_object.payment_intent
                
                if event_type == "checkout.session.completed":
                    success = True
                elif event_type == "checkout.session.expired":
                    success = False
            
            return StripeWebhookResult(
                valid=True,
                event_type=event_type,
                payment_intent_id=payment_intent_id,
                merchant_reference=merchant_reference,
                success=success,
                payment_method_type=payment_method_type,
                raw_data=event.data.object.to_dict() if hasattr(event.data.object, 'to_dict') else dict(event.data.object),
            )
            
        except stripe.error.SignatureVerificationError as e:
            return StripeWebhookResult(
                valid=False,
                error=f"Signature verification failed: {str(e)}"
            )
        except Exception as e:
            return StripeWebhookResult(
                valid=False,
                error=f"Failed to process webhook: {str(e)}"
            )
    
    def get_transaction_status_from_event(self, event_type: str, success: bool) -> TransactionStatus:
        """
        Map Stripe event types to internal transaction status.
        
        Args:
            event_type: Stripe event type
            success: Whether the event indicates success
            
        Returns:
            TransactionStatus enum value
        """
        if not success:
            return TransactionStatus.FAILED
        
        status_map = {
            "payment_intent.succeeded": TransactionStatus.CAPTURED,
            "payment_intent.created": TransactionStatus.PENDING,
            "payment_intent.processing": TransactionStatus.AUTHORIZED,
            "checkout.session.completed": TransactionStatus.CAPTURED,
        }
        
        return status_map.get(event_type, TransactionStatus.PENDING)
    
    def should_credit_player(self, event_type: str, success: bool) -> bool:
        """
        Determine if the player should be credited based on the event.
        
        Args:
            event_type: Stripe event type
            success: Whether the event indicates success
            
        Returns:
            True if player should be credited
        """
        # Credit on successful payment
        creditable_events = [
            "payment_intent.succeeded",
            "checkout.session.completed",
        ]
        return event_type in creditable_events and success
    
    def retrieve_payment_intent(self, payment_intent_id: str) -> Optional[dict]:
        """
        Retrieve a PaymentIntent by ID.
        
        Args:
            payment_intent_id: The PaymentIntent ID
            
        Returns:
            PaymentIntent data or None
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "metadata": dict(intent.metadata),
                "payment_method_types": intent.payment_method_types,
            }
        except stripe.error.StripeError:
            return None
    
    def register_apple_pay_domain(self, domain: str) -> dict:
        """
        Register a domain for Apple Pay.
        
        This can also be done via the Stripe Dashboard:
        Settings > Payment methods > Apple Pay > Add new domain
        
        Args:
            domain: The domain to register (e.g., 'example.com')
            
        Returns:
            Registration result
        """
        try:
            result = stripe.ApplePayDomain.create(domain_name=domain)
            return {"success": True, "domain": result.domain_name}
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}

