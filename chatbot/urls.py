
from django.urls import path
from .views import (
    StartChatSessionView,
    ChatbotApiView,
    ChatHistoryView,
    ChatHistoryDetailView
)

urlpatterns = [
    # Endpoint to start a new chat session
    path('start/', StartChatSessionView.as_view(), name='chatbot_start_session'),

    # Endpoint to send a message to an existing session
    path('message/', ChatbotApiView.as_view(), name='chatbot_message'),

    # Endpoint to get all saved chat sessions for a user
    path('history/', ChatHistoryView.as_view(), name='chatbot_history'),

    # Endpoint to retrieve or delete a specific chat session
    path('history/<uuid:session_id>/', ChatHistoryDetailView.as_view(), name='chatbot_history_detail'),
]
