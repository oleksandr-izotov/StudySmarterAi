from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone

class UserProfile(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('de', 'Deutsch'),
    ]
    TONE_CHOICES = [
        ('strict', 'Строгий'),
        ('friendly', 'Дружелюбный'),
    ]
    DEPTH_CHOICES = [
        ('short', 'Кратко'),
        ('detailed', 'Подробно'),
    ]
    FORMAT_CHOICES = [
        ('bullets', 'Список'),
        ('paragraphs', 'Параграфы'),
    ]
    GOAL_CHOICES = [
        ('exam', 'Экзамен'),
        ('homework', 'Домашнее задание'),
        ('understand', 'Понимание'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='ru')
    tone = models.CharField(max_length=10, choices=TONE_CHOICES, default='friendly')
    depth = models.CharField(max_length=10, choices=DEPTH_CHOICES, default='detailed')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='bullets')
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES, default='understand')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class MagicLinkToken(models.Model):
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"Magic Link for {self.email} ({'Valid' if self.is_valid() else 'Invalid'})"
