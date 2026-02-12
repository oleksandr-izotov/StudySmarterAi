from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import User
import uuid

class Prompt(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', _('Русский')),
        ('en', _('English')),
        ('de', _('Deutsch')),
    ]
    TONE_CHOICES = [
        ('strict', _('Строгий')),
        ('friendly', _('Дружелюбный')),
    ]
    DEPTH_CHOICES = [
        ('short', _('Кратко')),
        ('detailed', _('Подробно')),
    ]
    FORMAT_CHOICES = [
        ('bullets', _('Список')),
        ('paragraphs', _('Параграфы')),
    ]
    GOAL_CHOICES = [
        ('exam', _('Экзамен')),
        ('homework', _('Домашнее задание')),
        ('understand', _('Понимание')),
    ]
    STATUS_CHOICES = [
        ('pending', _('Ожидает')),
        ('done', _('Готово')),
        ('failed', _('Ошибка')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='prompts')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    text = models.TextField()
    
    # Settings
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='ru')
    tone = models.CharField(max_length=10, choices=TONE_CHOICES, default='friendly')
    depth = models.CharField(max_length=10, choices=DEPTH_CHOICES, default='detailed')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='bullets')
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES, default='understand')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    total_tokens = models.IntegerField(null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prompt {self.id} ({self.status})"

class Section(models.Model):
    TYPE_CHOICES = [
        ('explanation', _('Объяснение')),
        ('summary', _('Конспект')),
        ('plan', _('План')),
        ('quiz', _('Тест')),
    ]
    STATUS_CHOICES = [
        ('pending', _('Ожидает')),
        ('done', _('Готово')),
        ('failed', _('Ошибка')),
    ]

    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='sections')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    tokens_used = models.IntegerField(null=True, blank=True)
    version = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('prompt', 'type', 'version')

    def __str__(self):
        return f"Section {self.type} for {self.prompt.id}"
