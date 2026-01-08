"""
Views for Space Game Web App with Stripe Apple Pay integration.

Documentation: https://docs.stripe.com/apple-pay?platform=web
"""
import json
import uuid
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

import stripe

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Package definitions (mirror from backend)
PACKAGES = {
    "gold_100": {"price": 0.99, "gold_coins": 100, "health_packs": 0, "name": "100 Gold Coins"},
    "gold_500": {"price": 3.99, "gold_coins": 500, "health_packs": 0, "name": "500 Gold Coins"},
    "gold_1000": {"price": 6.99, "gold_coins": 1000, "health_packs": 0, "name": "1000 Gold Coins"},
    "health_pack_5": {"price": 1.99, "gold_coins": 0, "health_packs": 5, "name": "5 Health Packs"},
    "health_pack_10": {"price": 2.99, "gold_coins": 0, "health_packs": 10, "name": "10 Health Packs"},
    "starter_bundle": {"price": 9.99, "gold_coins": 1500, "health_packs": 20, "name": "Starter Bundle"},
}


def get_or_create_player_uuid(request):
    """Get player UUID from session or create a new one."""
    if 'player_uuid' not in request.session:
        request.session['player_uuid'] = str(uuid.uuid4())
    return request.session['player_uuid']


def landing_page(request):
    """
    Main landing page for the Space Game.
    """
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'packages': [
            {
                'id': pkg_id,
                'name': pkg['name'],
                'price': pkg['price'],
                'gold_coins': pkg['gold_coins'],
                'health_packs': pkg['health_packs'],
            }
            for pkg_id, pkg in PACKAGES.items()
        ],
    }
    return render(request, 'landing.html', context)


def shop_page(request):
    """
    Shop page with all available packages.
    """
    player_uuid = get_or_create_player_uuid(request)
    
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'player_uuid': player_uuid,
        'packages': [
            {
                'id': pkg_id,
                'name': pkg['name'],
                'price': pkg['price'],
                'gold_coins': pkg['gold_coins'],
                'health_packs': pkg['health_packs'],
            }
            for pkg_id, pkg in PACKAGES.items()
        ],
    }
    return render(request, 'shop.html', context)


def package_detail(request, package_id):
    """
    Detail page for a specific package with Stripe Express Checkout (Apple Pay).
    """
    if package_id not in PACKAGES:
        return redirect('shop')
    
    player_uuid = get_or_create_player_uuid(request)
    package = PACKAGES[package_id]
    
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'player_uuid': player_uuid,
        'package_id': package_id,
        'package': {
            'id': package_id,
            'name': package['name'],
            'price': package['price'],
            'gold_coins': package['gold_coins'],
            'health_packs': package['health_packs'],
        },
    }
    return render(request, 'package_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_payment_intent(request):
    """
    Create a Stripe PaymentIntent for Apple Pay / Express Checkout Element.
    
    This endpoint is called from the frontend when the user initiates payment.
    The client_secret is returned to confirm the payment on the client.
    
    Apple Pay Requirements (per Stripe docs):
    1. Domain must be registered with Stripe for Apple Pay
    2. Site must be served over HTTPS (except localhost for testing)
    3. Use Express Checkout Element on frontend
    """
    try:
        data = json.loads(request.body)
        package_id = data.get('package_id')
        player_uuid = data.get('player_uuid') or get_or_create_player_uuid(request)
        email = data.get('email')
        
        if package_id not in PACKAGES:
            return JsonResponse({'error': 'Invalid package'}, status=400)
        
        package = PACKAGES[package_id]
        amount_cents = int(package['price'] * 100)
        
        # Generate unique reference
        merchant_reference = f"{player_uuid[:8]}_{package_id}_{uuid.uuid4().hex[:8]}"
        
        # Create PaymentIntent with automatic payment methods enabled
        # This enables Apple Pay, Google Pay, and cards
        intent_params = {
            'amount': amount_cents,
            'currency': 'usd',
            'automatic_payment_methods': {
                'enabled': True,
            },
            'metadata': {
                'player_uuid': player_uuid,
                'package_id': package_id,
                'merchant_reference': merchant_reference,
                'gold_coins': str(package['gold_coins']),
                'health_packs': str(package['health_packs']),
            },
            'description': package['name'],
        }
        
        if email:
            intent_params['receipt_email'] = email
        
        payment_intent = stripe.PaymentIntent.create(**intent_params)
        
        return JsonResponse({
            'clientSecret': payment_intent.client_secret,
            'paymentIntentId': payment_intent.id,
            'merchantReference': merchant_reference,
        })
        
    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_checkout_session(request):
    """
    Create a Stripe Checkout Session (hosted payment page).
    
    Apple Pay is automatically available in Checkout when enabled in Dashboard.
    """
    try:
        data = json.loads(request.body)
        package_id = data.get('package_id')
        player_uuid = data.get('player_uuid') or get_or_create_player_uuid(request)
        
        if package_id not in PACKAGES:
            return JsonResponse({'error': 'Invalid package'}, status=400)
        
        package = PACKAGES[package_id]
        amount_cents = int(package['price'] * 100)
        merchant_reference = f"{player_uuid[:8]}_{package_id}_{uuid.uuid4().hex[:8]}"
        
        # Build URLs
        domain = request.build_absolute_uri('/').rstrip('/')
        success_url = f"{domain}/payment/success/?ref={merchant_reference}&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{domain}/payment/cancelled/?ref={merchant_reference}"
        
        session = stripe.checkout.Session.create(
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': package['name'],
                            'description': f"Gold Coins: {package['gold_coins']}, Health Packs: {package['health_packs']}",
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }
            ],
            metadata={
                'player_uuid': player_uuid,
                'package_id': package_id,
                'merchant_reference': merchant_reference,
                'gold_coins': str(package['gold_coins']),
                'health_packs': str(package['health_packs']),
            },
        )
        
        return JsonResponse({
            'sessionId': session.id,
            'url': session.url,
        })
        
    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    
    Configure this endpoint in Stripe Dashboard:
    Developers > Webhooks > Add endpoint
    
    Listen for these events:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - checkout.session.completed
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    
    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            # For testing without webhook signature verification
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
        
        event_type = event.type
        data_object = event.data.object
        
        # Handle successful payment
        if event_type == 'payment_intent.succeeded':
            metadata = data_object.metadata
            player_uuid = metadata.get('player_uuid')
            package_id = metadata.get('package_id')
            
            # Here you would call your backend API to credit the player
            # Example: requests.post(f"{settings.BACKEND_API_URL}/api/wallet/credit", ...)
            print(f"Payment succeeded for player {player_uuid}, package {package_id}")
        
        elif event_type == 'checkout.session.completed':
            metadata = data_object.metadata
            player_uuid = metadata.get('player_uuid')
            package_id = metadata.get('package_id')
            
            print(f"Checkout completed for player {player_uuid}, package {package_id}")
        
        elif event_type == 'payment_intent.payment_failed':
            print(f"Payment failed: {data_object.id}")
        
        return HttpResponse(status=200)
        
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    except Exception as e:
        print(f"Webhook error: {e}")
        return HttpResponse(status=400)


def payment_success(request):
    """
    Success page after payment completion.
    """
    ref = request.GET.get('ref', '')
    session_id = request.GET.get('session_id', '')
    
    context = {
        'merchant_reference': ref,
        'session_id': session_id,
    }
    return render(request, 'payment_success.html', context)


def payment_cancelled(request):
    """
    Page shown when payment is cancelled.
    """
    ref = request.GET.get('ref', '')
    
    context = {
        'merchant_reference': ref,
    }
    return render(request, 'payment_cancelled.html', context)

