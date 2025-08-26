
from django.urls import path
from .views import MindsetCoachApiView

urlpatterns = [
    path('', MindsetCoachApiView.as_view(), name='mindset_coach_api'),
]
