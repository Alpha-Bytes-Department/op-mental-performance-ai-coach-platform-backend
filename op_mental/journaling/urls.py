from django.urls import path
from .views import (
    JournalingChatView,
    JournalSessionListView,
    JournalSessionDetailView,
    JournalingStatisticsView,
)

urlpatterns = [
    path('journaling/chat/', JournalingChatView.as_view(), name='journaling-chat'),
    path('journaling/sessions/', JournalSessionListView.as_view(), name='journal-session-list'),
    path('journaling/sessions/<int:pk>/', JournalSessionDetailView.as_view(), name='journal-session-detail'),
    path('journaling/statistics/', JournalingStatisticsView.as_view(), name='journaling-statistics'),
]