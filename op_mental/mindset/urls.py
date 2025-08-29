
from django.urls import path
from .views import MindsetCoachApiView, MindsetHistoryView

urlpatterns = [
    path('', MindsetCoachApiView.as_view(), name='mindset_coach_api'),
    path('history/<int:session_id>/', MindsetHistoryView.as_view(), name='mindset_history_api'),
]
