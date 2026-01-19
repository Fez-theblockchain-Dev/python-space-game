"""
URL configuration for Space Game Web App.

API Endpoints:
==============
Payment APIs (Stripe):
    POST /api/create-payment-intent/     - Create PaymentIntent for Apple Pay / Express Checkout
    POST /api/create-checkout-session/   - Create Stripe Checkout session (hosted page)
    POST /api/stripe-webhook/            - Webhook handler for Stripe events

Wallet APIs:
    GET  /api/wallet/balance/            - Get player's wallet balance
    GET  /api/packages/                  - Get available packages for purchase
    GET  /api/transactions/              - Get player's transaction history

Pages:
    GET  /                               - Landing page with store
    GET  /shop/                          - Shop page
    GET  /shop/<package_id>/             - Package detail page with Express Checkout
    GET  /payment/success/               - Success page after payment
    GET  /payment/cancelled/             - Cancelled payment page
"""
from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing'),
    
    # Shop / Store pages
    path('shop/', views.shop_page, name='shop'),
    path('shop/<str:package_id>/', views.package_detail, name='package_detail'),
    
    # Stripe Payment endpoints
    path('api/create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('api/create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('api/stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Wallet and Economy endpoints
    path('api/wallet/balance/', views.get_wallet_balance, name='wallet_balance'),
    path('api/packages/', views.get_packages, name='packages'),
    path('api/transactions/', views.get_transaction_history, name='transactions'),
    
    # Payment result pages
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancelled/', views.payment_cancelled, name='payment_cancelled'),
]

