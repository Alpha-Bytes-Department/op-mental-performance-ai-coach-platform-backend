from rest_framework import serializers

class ChallengeRequestSerializer(serializers.Serializer):
    """Serializer for incoming chat messages."""
    message = serializers.CharField()
    session_id = serializers.UUIDField(required=False, allow_null=True)

class ChallengeResponseSerializer(serializers.Serializer):
    """Serializer for outgoing chatbot responses."""
    session_id = serializers.UUIDField()
    is_session_complete = serializers.BooleanField()
    response_type = serializers.CharField() # e.g., 'question', 'validation_error', 'phase_summary', 'final_summary'
    question = serializers.CharField(allow_null=True)
    phase = serializers.CharField()
    phase_goal = serializers.CharField()
    error_message = serializers.CharField(allow_null=True)
    summary = serializers.CharField(allow_null=True)
