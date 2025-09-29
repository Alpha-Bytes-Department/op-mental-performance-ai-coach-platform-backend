
from django.db import models
from django.conf import settings

class MindsetSession(models.Model):
    """Represents a single session with the Mindset Coach."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_step = models.IntegerField(default=1)
    user_responses = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mindset Session {self.id} for {self.user.username} at step {self.current_step}"

class MindsetMessage(models.Model):
    """Represents a single message exchange in a MindsetSession."""
    session = models.ForeignKey(MindsetSession, related_name='messages', on_delete=models.CASCADE)
    user_message = models.TextField()
    coach_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Exchange in session {self.session.id} at {self.timestamp}"

    class Meta:
        ordering = ['timestamp']
