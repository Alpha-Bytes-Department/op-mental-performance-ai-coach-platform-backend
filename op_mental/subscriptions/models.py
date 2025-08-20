from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator

class SubscriptionPlan(models.Model):
    PLAN_TYPES = (
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('pro', 'Pro'),
    )
    name = models.CharField(max_length=50, choices=PLAN_TYPES, unique=True)
    description = models.TextField()
    features = models.TextField(help_text="List features line by line, e.g. use '\\n' for new line.", blank=True, default="")
    recommended = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    duration_days = models.IntegerField(validators=[MinValueValidator(1)])
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_plans'

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('canceled', 'Canceled'),
    )
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'user_subscriptions'

    def save(self, *args, **kwargs):
        if not self.end_date or self.end_date < timezone.now():
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        if self.status == 'pending' and self.end_date > timezone.now():
            self.status = 'active'
        super().save(*args, **kwargs)

    def is_active(self):
        return self.status == 'active' and self.end_date > timezone.now()

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"