"""
URL configuration for Space Game Web App.
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
    
    # Payment result pages
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancelled/', views.payment_cancelled, name='payment_cancelled'),
]

