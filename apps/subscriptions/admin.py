from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, UsageLog, PaymentEvent


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'name',
        'limit_count',
        'limit_period',
        'monthly_price',
        'is_paid',
        'is_active',
        'sort_order',
        'stripe_price_id',
    ]
    list_filter = ['is_paid', 'is_active', 'limit_period']
    list_editable = ['is_active', 'sort_order', 'stripe_price_id']
    ordering = ['sort_order']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'plan',
        'started_at',
        'expires_at',
        'is_active',
        'is_expired',
        'stripe_customer_id',
        'stripe_subscription_id',
    ]
    list_filter = ['plan', 'is_active']
    search_fields = ['user__username', 'user__email', 'stripe_customer_id']
    raw_id_fields = ['user']
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = [
        'get_identifier',
        'prompt',
        'created_at',
    ]
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_key']
    raw_id_fields = ['user', 'prompt']
    date_hierarchy = 'created_at'
    
    def get_identifier(self, obj):
        if obj.user:
            return obj.user.username
        return f"Guest:{obj.session_key[:8]}..."
    get_identifier.short_description = 'User/Session'


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_id',
        'event_type',
        'processed',
        'created_at',
    ]
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['event_id', 'event_type']
    readonly_fields = ['event_id', 'event_type', 'payload', 'created_at']
    date_hierarchy = 'created_at'

