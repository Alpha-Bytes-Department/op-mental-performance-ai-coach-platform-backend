from django.db import models
from django.conf import settings

class JournalSession(models.Model):
    CATEGORY_CHOICES = (
        ('personal_win', 'Personal Win'),
        ('personal_challenge', 'Personal Challenge'),
        ('professional_win', 'Professional Win'),
        ('professional_challenge', 'Professional Challenge'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    session_data = models.JSONField(null=True, blank=True)


    def __str__(self):
        return f"Journal session by {self.user} on {self.created_at.strftime('%Y-%m-%d')}"

class JournalEntry(models.Model):
    session = models.ForeignKey(JournalSession, related_name='entries', on_delete=models.CASCADE)
    author = models.CharField(max_length=10) # 'user' or 'bot'
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author}: {self.message[:50]}"