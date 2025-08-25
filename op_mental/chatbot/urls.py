
from django.urls import path
from .views import ChatbotApiView

urlpatterns = [
    path('', ChatbotApiView.as_view(), name='chatbot_api'),
]
