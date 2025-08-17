from django.urls import path
from .views import JournalListCreateView, JournalDetailView

urlpatterns = [
    path('journals/', JournalListCreateView.as_view(), name='journal-list-create'),
    path('journals/<int:pk>/', JournalDetailView.as_view(), name='journal-detail'),
]