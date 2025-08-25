
from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    """Serializer for the incoming chat request."""
    message = serializers.CharField()
    session_id = serializers.IntegerField(required=False, help_text="The ID of the current chat session. If not provided, a new session will be created.")
    age_group = serializers.ChoiceField(choices=["youth", "adult", "masters"], default="adult")

class ChatResponseSerializer(serializers.Serializer):
    """Serializer for the chatbot's response."""
    reply = serializers.CharField()
    session_id = serializers.IntegerField()
