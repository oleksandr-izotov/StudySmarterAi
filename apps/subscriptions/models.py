from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class SubscriptionPlan(models.Model):
    PERIOD_CHOICES = [
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly'),
    ]

    name = models.CharField(max_length=20, unique=True)
    display_name = models.CharField(max_length=50)
    limit_count = models.PositiveIntegerField(null=True, blank=True)
    limit_period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='day')
    monthly_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.display_name

    @property
    def is_unlimited(self):
        return self.limit_count is None

    def get_period_start(self):
        now = timezone.now()
        if self.limit_period == 'day':
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.limit_period == 'week':
            start = now - timedelta(days=now.weekday())
            return start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.limit_period == 'month':
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return now


class UserSubscription(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscribers'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.display_name}"

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at


class UsageLog(models.Model):
    ACTION_TYPES = [
        ('prompt', 'New Prompt'),
        ('regenerate', 'Regeneration'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='usage_logs'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    prompt = models.ForeignKey(
        'prompts.Prompt',
        on_delete=models.CASCADE,
        related_name='usage_logs',
        null=True,
        blank=True
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, default='prompt')
    cost = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_key', 'created_at']),
        ]

    def __str__(self):
        identifier = self.user.username if self.user else f"Guest:{self.session_key[:8]}"
        return f"{identifier} - {self.action_type} ({self.cost}) - {self.created_at}"


class PaymentEvent(models.Model):
    event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=100)
    processed = models.BooleanField(default=False)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.event_id[:20]}..."
