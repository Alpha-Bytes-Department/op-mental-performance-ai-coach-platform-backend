from rest_framework import serializers
from .models import ChatMessage, ChatSession

class StartChatSessionSerializer(serializers.Serializer):
    """Serializer for starting a new chat session."""
    save_history = serializers.BooleanField(default=False)

class ChatRequestSerializer(serializers.Serializer):
    """Serializer for the incoming chat request."""
    message = serializers.CharField()
    session_id = serializers.UUIDField(required=True)
    age_group = serializers.ChoiceField(choices=["youth", "adult", "masters"], default="adult")

class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for a single chat message."""
    class Meta:
        model = ChatMessage
        fields = ['role', 'message', 'created_at']

class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for listing chat sessions."""
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'created_at', 'updated_at']

class ChatResponseSerializer(serializers.Serializer):
    """Serializer for the chatbot's response."""
    reply = serializers.CharField()
    session_id = serializers.UUIDField()