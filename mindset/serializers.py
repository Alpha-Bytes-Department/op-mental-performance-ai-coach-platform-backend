
from rest_framework import serializers

class MindsetRequestSerializer(serializers.Serializer):
    """Serializer for the incoming mindset coach request."""
    message = serializers.CharField()
    session_id = serializers.IntegerField(required=False, help_text="The ID of the current session. If not provided, a new session will be created.")

class MindsetResponseSerializer(serializers.Serializer):
    """Serializer for the mindset coach's response."""
    reply = serializers.CharField()
    session_id = serializers.IntegerField()
    current_step = serializers.IntegerField()
    is_complete = serializers.BooleanField()
