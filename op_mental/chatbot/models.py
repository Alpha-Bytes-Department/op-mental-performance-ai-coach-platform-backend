from django.db import models
from django.conf import settings
import uuid

class RedisChatSession(models.Model):
    """
    A simple model to map a user to a Redis-based chat session ID.
    The actual chat messages are stored in Redis, not here.
    """
    # Use a UUID field for the session ID to match what Redis uses.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Redis Chat Session {self.id} for {self.user.username}"