from django.db import models
from django.conf import settings

class Journal(models.Model):
    ENTRY_POINT_CHOICES = (
        ('positive_trigger', 'Positive Trigger'),
        ('negative_trigger', 'Negative Trigger'),
        ('recurring_thought', 'Recurring Thought'),
        ('future_goal', 'Future Goal'),
        ('milestone_gratitude', 'Milestone Gratitude'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entry_point_type = models.CharField(max_length=50, choices=ENTRY_POINT_CHOICES)
    entry_point_description = models.TextField(blank=True, null=True)
    layer1_facts = models.TextField(blank=True, null=True)
    layer2_emotions = models.TextField(blank=True, null=True)
    layer3_beliefs = models.TextField(blank=True, null=True)
    perspective_expansion = models.TextField(blank=True, null=True)
    value_connection = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Journal entry by {self.user} on {self.created_at.strftime('%Y-%m-%d')}"