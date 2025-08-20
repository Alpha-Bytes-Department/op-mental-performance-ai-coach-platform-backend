from django.urls import path
from .views import SubscriptionPlanViewSet, UserSubscriptionViewSet, CreateCheckoutSessionView, stripe_webhook, VerifySubscriptionView

app_name = 'subscriptions'

urlpatterns = [
    # SubscriptionPlan URLs
    path('plans/', SubscriptionPlanViewSet.as_view({'get': 'list', 'post': 'create'}), name='subscriptionplan-list'),
    path('plans/<int:pk>/', SubscriptionPlanViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='subscriptionplan-detail'),

    # UserSubscription URLs
    path('user-subscriptions/', UserSubscriptionViewSet.as_view({'get': 'list', 'post': 'create'}), name='usersubscription-list'),
    path('user-subscriptions/<int:pk>/', UserSubscriptionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='usersubscription-detail'),

    # Stripe related URLs
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('stripe-webhook/', stripe_webhook, name='stripe-webhook'),
    path('verify-subscription/', VerifySubscriptionView.as_view(), name='verify-subscription'),

    # Placeholder URLs for success and cancel (frontend will handle these)
    path('success/', CreateCheckoutSessionView.as_view(), name='success'), # Placeholder
    path('cancel/', CreateCheckoutSessionView.as_view(), name='cancel'),   # Placeholder
]