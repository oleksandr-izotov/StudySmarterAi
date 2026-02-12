from django.contrib import admin
from .models import Prompt, Section

class SectionInline(admin.StackedInline):
    model = Section
    extra = 0
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'short_text', 'status', 'created_at', 'language')
    list_filter = ('status', 'language', 'created_at', 'goal')
    search_fields = ('text', 'user__username', 'session_key')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [SectionInline]

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Text'

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'prompt', 'type', 'status', 'version')
    list_filter = ('status', 'type')
    search_fields = ('content',)
    readonly_fields = ('created_at', 'updated_at')
