from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from .models import SubscriptionPlan, UserSubscription, UsageLog


class SubscriptionService:
    
    DEFAULT_FREE_PLAN = 'free'
    DEFAULT_GUEST_PLAN = 'guest'

    @classmethod
    def get_or_create_default_plans(cls):
        plans_data = [
            {
                'name': 'guest',
                'display_name': 'Guest',
                'limit_count': 5,
                'limit_period': 'month',
                'monthly_price': 0,
                'is_paid': False,
                'sort_order': 0,
            },
            {
                'name': 'free',
                'display_name': 'Free',
                'limit_count': 10,
                'limit_period': 'week',
                'monthly_price': 0,
                'is_paid': False,
                'sort_order': 1,
            },
            {
                'name': 'pro',
                'display_name': 'Pro',
                'limit_count': 50,
                'limit_period': 'day',
                'monthly_price': 15,
                'is_paid': True,
                'sort_order': 2,
            },
            {
                'name': 'pro_plus',
                'display_name': 'Pro+',
                'limit_count': 200,
                'limit_period': 'day',
                'monthly_price': 40,
                'is_paid': True,
                'sort_order': 3,
            },
        ]
        
        for data in plans_data:
            SubscriptionPlan.objects.update_or_create(
                name=data['name'],
                defaults=data
            )

    @classmethod
    def get_user_plan(cls, user, session_key=None):
        if user and user.is_authenticated:
            try:
                subscription = user.subscription
                if subscription.is_active and not subscription.is_expired:
                    return subscription.plan
            except UserSubscription.DoesNotExist:
                pass
            
            free_plan = SubscriptionPlan.objects.filter(
                name=cls.DEFAULT_FREE_PLAN,
                is_active=True
            ).first()
            return free_plan
        
        guest_plan = SubscriptionPlan.objects.filter(
            name=cls.DEFAULT_GUEST_PLAN,
            is_active=True
        ).first()
        return guest_plan

    @classmethod
    def assign_free_plan(cls, user):
        free_plan = SubscriptionPlan.objects.filter(
            name=cls.DEFAULT_FREE_PLAN,
            is_active=True
        ).first()
        
        if free_plan:
            UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': free_plan,
                    'is_active': True,
                    'expires_at': None,
                }
            )


class UsageService:

    @classmethod
    def get_usage_count(cls, user, session_key, plan):
        if plan is None:
            return Decimal('0')
        
        period_start = plan.get_period_start()
        
        if user and user.is_authenticated:
            result = UsageLog.objects.filter(
                user=user,
                created_at__gte=period_start
            ).aggregate(total=Sum('cost'))
        elif session_key:
            result = UsageLog.objects.filter(
                session_key=session_key,
                created_at__gte=period_start
            ).aggregate(total=Sum('cost'))
        else:
            return Decimal('0')
        
        return result['total'] or Decimal('0')

    @classmethod
    def get_remaining_requests(cls, user, session_key):
        plan = SubscriptionService.get_user_plan(user, session_key)
        
        if plan is None:
            return Decimal('0')
        
        if plan.is_unlimited:
            return float('inf')
        
        used = cls.get_usage_count(user, session_key, plan)
        remaining = Decimal(plan.limit_count) - used
        return max(Decimal('0'), remaining)

    @classmethod
    def can_make_request(cls, user, session_key, cost=Decimal('1.0')):
        plan = SubscriptionService.get_user_plan(user, session_key)
        
        if plan is None:
            return False
        
        if plan.is_unlimited:
            return True
        
        used = cls.get_usage_count(user, session_key, plan)
        return used + cost <= Decimal(plan.limit_count)

    @classmethod
    def record_usage(cls, user, session_key, prompt, action_type='prompt', cost=Decimal('1.0')):
        UsageLog.objects.create(
            user=user if user and user.is_authenticated else None,
            session_key=session_key if not (user and user.is_authenticated) else None,
            prompt=prompt,
            action_type=action_type,
            cost=cost
        )

    @classmethod
    def record_regeneration(cls, user, session_key, prompt=None):
        cls.record_usage(
            user=user,
            session_key=session_key,
            prompt=prompt,
            action_type='regenerate',
            cost=Decimal('0.5')
        )

    @classmethod
    def get_usage_stats(cls, user, session_key):
        plan = SubscriptionService.get_user_plan(user, session_key)
        
        if plan is None:
            return {
                'plan': None,
                'used': 0,
                'limit': 0,
                'remaining': 0,
                'period': None,
            }
        
        used = cls.get_usage_count(user, session_key, plan)
        limit = plan.limit_count if not plan.is_unlimited else None
        remaining = cls.get_remaining_requests(user, session_key)
        
        return {
            'plan': plan,
            'used': float(used),
            'limit': limit,
            'remaining': float(remaining) if remaining != float('inf') else None,
            'period': plan.limit_period,
            'is_unlimited': plan.is_unlimited,
        }

