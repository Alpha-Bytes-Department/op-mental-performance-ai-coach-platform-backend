from django.urls import path
from .views import ChallengeAPIView

app_name = 'internal_challenge'

urlpatterns = [
    path('', ChallengeAPIView.as_view(), name='challenge-chat'),
]
