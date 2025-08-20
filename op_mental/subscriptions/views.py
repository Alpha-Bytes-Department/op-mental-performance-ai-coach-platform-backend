import stripe
import logging
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

logger = logging.getLogger(__name__)

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]

class UserSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_anonymous and getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"message": "You do not have any active subscriptions."})
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        plan_id = request.data.get('plan_id')
        if not plan_id:
            logger.error("No plan_id provided in checkout session request")
            return Response({'error': 'Plan ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/subscriptions/cancel",
                client_reference_id=str(request.user.id),
                metadata={'plan_id': plan_id},
            )
            logger.info(f"Checkout session created for user ID: {request.user.id}, email: {request.user.email}, session ID: {checkout_session.id}")
            return Response({
    'sessionId': checkout_session.id,
    'url': checkout_session.url  # ✅ This is the actual Checkout URL you can open in browser
}, status=status.HTTP_200_OK)
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Plan {plan_id} not found")
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error for user {request.user.id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error for user {request.user.id}: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                # Optional: Check if the subscription record is created, though the webhook is the primary mechanism.
                return Response({'status': 'success', 'message': 'Payment verified.'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'failed', 'message': 'Payment not successful.'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying session {session_id} for user {request.user.id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error verifying session {session_id} for user {request.user.id}: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        plan_id = session.get('metadata', {}).get('plan_id')
        logger.info(f"Webhook received: checkout.session.completed. user_id: {user_id}, plan_id: {plan_id}")

        if user_id and plan_id:
            try:
                user = get_user_model().objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
                logger.info(f"Webhook: Found user {user.email} and plan {plan.name}")
                end_date = timezone.now() + timezone.timedelta(days=plan.duration_days)
                UserSubscription.objects.create(
                    user=user,
                    plan=plan,
                    end_date=end_date,
                    status='active',
                    stripe_subscription_id=session['subscription']
                )
                logger.info(f"Subscription created for user {user_id}, plan {plan_id}")
            except (SubscriptionPlan.DoesNotExist, get_user_model().DoesNotExist) as e:
                logger.error(f"Webhook error: User or Plan not found for user_id={user_id}, plan_id={plan_id}. Error: {str(e)}")
                return HttpResponse(status=400)
            except Exception as e:
                logger.error(f"Webhook unexpected error for user_id={user_id}, plan_id={plan_id}. Error: {str(e)}")
                return HttpResponse(status=500)

    return HttpResponse(status=200)