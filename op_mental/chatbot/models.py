
from django.db import models
from django.conf import settings

class ChatSession(models.Model):
    """Represents a single, continuous conversation session with the chatbot."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat Session {self.id} for user {self.user.username}"

class ChatMessage(models.Model):
    """Represents a single user message and the bot's response within a session."""
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    user_message = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Exchange in session {self.session.id} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['timestamp']
