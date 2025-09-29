from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class ChallengeSession(models.Model):
    """Stores the state of an internal challenge therapy session for a user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenge_sessions')
    
    # State of the therapy system
    session_data = models.JSONField(default=dict)
    conversation_history = models.JSONField(default=list)
    current_phase = models.CharField(max_length=50)
    challenge_type = models.CharField(max_length=50, default='General Challenge')
    current_question_index = models.PositiveIntegerField(default=0)
    summary = models.TextField(null=True, blank=True)
    
    # Session metadata
    is_complete = models.BooleanField(default=False)
    session_started = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Challenge Session for {self.user.username} started at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-created_at']
        db_table = 'challenge_sessions'