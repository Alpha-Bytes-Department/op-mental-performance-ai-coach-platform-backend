from django.urls import path
from .views import ChallengeAPIView, ChallengeHistoryView

app_name = 'internal_challenge'

urlpatterns = [
    path('', ChallengeAPIView.as_view(), name='challenge-chat'),
    path('<uuid:session_id>/', ChallengeHistoryView.as_view(), name='challenge-history'),
]
