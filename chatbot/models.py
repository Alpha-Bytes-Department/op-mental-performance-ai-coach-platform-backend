from django.db import models
from django.conf import settings

class UserChatCounter(models.Model):
    """Tracks the number of chat messages sent by a non-subscribed user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_counter'
    )
    message_count = models.PositiveIntegerField(
        default=0,
        help_text="Counts messages for non-subscribed users."
    )

    def __str__(self):
        return f"{self.user.username} - Messages: {self.message_count}"

    class Meta:
        db_table = 'user_chat_counters'

import uuid
from django.conf import settings
from django.db import models

class ChatSession(models.Model):
    """Stores a chat session, with an option to save the history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=100, blank=True, null=True)
    save_history = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ChatSession {self.id} for {self.user.username}"

class ChatMessage(models.Model):
    """Stores a single message within a chat session."""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('assistant', 'Assistant')])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.message[:50]}"

    class Meta:
        ordering = ['created_at']