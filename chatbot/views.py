from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import ChatSession, ChatMessage, UserChatCounter, ChatbotSettings
from .serializers import (
    StartChatSessionSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatSessionSerializer,
    ChatMessageSerializer,
    ChatbotSettingsSerializer
)
from .chatbot_logic import GeneralChatSystem
from subscriptions.models import UserSubscription
from django.utils import timezone


class StartChatSessionView(APIView):
    """API view to start a new chat session."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = StartChatSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        global_settings = ChatbotSettings.get_settings()

        if not global_settings.allow_chat_history:
            save_history = False
        else:
            save_history = serializer.validated_data.get('save_history', False)

        session = ChatSession.objects.create(user=request.user, save_history=save_history)
        return Response({'session_id': session.id}, status=status.HTTP_201_CREATED)


class ChatbotApiView(APIView):
    """API view to interact with the chatbot."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        user = request.user
        session_id = validated_data.get('session_id')
        user_message = validated_data['message']
        age_group = validated_data.get('age_group')

        session = get_object_or_404(ChatSession, id=session_id, user=user)

        has_active_subscription = UserSubscription.objects.filter(
            user=user,
            status='active',
            end_date__gte=timezone.now()
        ).exists()

        if not has_active_subscription:
            counter, created = UserChatCounter.objects.get_or_create(user=user)
            if counter.message_count >= 0:
                return Response(
                    {"reply": "Subscription Required !", "session_id": session_id},
                    status=status.HTTP_208_ALREADY_REPORTED
                )
            counter.message_count += 1
            counter.save()

        if not session.title and session.save_history:
            session.title = ' '.join(user_message.split()[:5])
            session.save()

        history = []
        if session.save_history:
            history = session.messages.all()

        formatted_history = []
        for item in history:
            formatted_history.append({
                "user_message": item.message if item.role == 'user' else None,
                "bot_response": item.message if item.role == 'assistant' else None,
                "full_conversation": f"User: {item.message if item.role == 'user' else ''}\nBot: {item.message if item.role == 'assistant' else ''}"
            })

        chat_system = GeneralChatSystem()
        chat_system.load_history(formatted_history)
        bot_response = chat_system.get_response(user_message, age_group)

        if session.save_history:
            ChatMessage.objects.create(session=session, role='user', message=user_message)
            ChatMessage.objects.create(session=session, role='assistant', message=bot_response)

        response_serializer = ChatResponseSerializer({
            'reply': bot_response,
            'session_id': session_id
        })

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ChatHistoryView(APIView):
    """API view to list all saved chat sessions for a user."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        sessions = ChatSession.objects.filter(user=request.user, save_history=True).order_by('-updated_at')
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatHistoryDetailView(APIView):
    """API view to retrieve or delete a specific chat session."""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        messages = session.messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatbotSettingsView(APIView):
    """API view to expose chatbot global settings (for frontend use)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        settings_instance = ChatbotSettings.get_settings()
        serializer = ChatbotSettingsSerializer(settings_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
