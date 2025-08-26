
from django.urls import path
from .views import ChatbotApiView, AllUserChatHistoryView

urlpatterns = [
    # Endpoint to send a message and get a reply
    path('', ChatbotApiView.as_view(), name='chatbot_api'),
    
    # Endpoint to fetch all of a user's chat history from the last 24 hours
    path('history/all/', AllUserChatHistoryView.as_view(), name='chatbot_all_history_api'),
]
