from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.subscriptions.models import SubscriptionPlan, UserSubscription, UsageLog
from apps.subscriptions.services import SubscriptionService, UsageService
from apps.prompts.models import Prompt
from django.utils import timezone
from datetime import timedelta


class SubscriptionPlanTests(TestCase):

    def setUp(self):
        SubscriptionService.get_or_create_default_plans()

    def test_default_plans_created(self):
        plans = SubscriptionPlan.objects.all()
        self.assertEqual(plans.count(), 4)

    def test_guest_plan_config(self):
        guest = SubscriptionPlan.objects.get(name='guest')
        self.assertEqual(guest.limit_count, 5)
        self.assertEqual(guest.limit_period, 'month')
        self.assertEqual(guest.monthly_price, 0)

    def test_free_plan_config(self):
        free = SubscriptionPlan.objects.get(name='free')
        self.assertEqual(free.limit_count, 10)
        self.assertEqual(free.limit_period, 'week')
        self.assertEqual(free.monthly_price, 0)

    def test_pro_plan_config(self):
        pro = SubscriptionPlan.objects.get(name='pro')
        self.assertEqual(pro.limit_count, 50)
        self.assertEqual(pro.limit_period, 'day')
        self.assertEqual(pro.monthly_price, 15)

    def test_pro_plus_plan_config(self):
        pro_plus = SubscriptionPlan.objects.get(name='pro_plus')
        self.assertEqual(pro_plus.limit_count, 200)
        self.assertEqual(pro_plus.limit_period, 'day')
        self.assertEqual(pro_plus.monthly_price, 40)


class UserSubscriptionTests(TestCase):

    def setUp(self):
        SubscriptionService.get_or_create_default_plans()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_new_user_gets_free_plan(self):
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.plan.name, 'free')
        self.assertTrue(subscription.is_active)

    def test_get_user_plan_authenticated(self):
        plan = SubscriptionService.get_user_plan(self.user)
        self.assertEqual(plan.name, 'free')

    def test_get_user_plan_guest(self):
        plan = SubscriptionService.get_user_plan(None, 'session123')
        self.assertEqual(plan.name, 'guest')


class UsageTrackingTests(TestCase):

    def setUp(self):
        SubscriptionService.get_or_create_default_plans()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.prompt = Prompt.objects.create(
            user=self.user,
            text='Test prompt',
            status='done'
        )

    def test_record_usage_authenticated(self):
        UsageService.record_usage(self.user, None, self.prompt)
        count = UsageLog.objects.filter(user=self.user).count()
        self.assertEqual(count, 1)

    def test_record_usage_guest(self):
        UsageService.record_usage(None, 'session123', self.prompt)
        count = UsageLog.objects.filter(session_key='session123').count()
        self.assertEqual(count, 1)

    def test_get_remaining_requests_free_user(self):
        remaining = UsageService.get_remaining_requests(self.user, None)
        self.assertEqual(remaining, 10)

    def test_remaining_decreases_after_usage(self):
        UsageService.record_usage(self.user, None, self.prompt)
        remaining = UsageService.get_remaining_requests(self.user, None)
        self.assertEqual(remaining, 9)


class RateLimitTests(TestCase):

    def setUp(self):
        SubscriptionService.get_or_create_default_plans()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_can_make_request_within_limit(self):
        can_request = UsageService.can_make_request(self.user, None)
        self.assertTrue(can_request)

    def test_cannot_make_request_when_limit_exceeded(self):
        free_plan = SubscriptionPlan.objects.get(name='free')
        
        for i in range(free_plan.limit_count):
            prompt = Prompt.objects.create(
                user=self.user,
                text=f'Test prompt {i}',
                status='done'
            )
            UsageService.record_usage(self.user, None, prompt)
        
        can_request = UsageService.can_make_request(self.user, None)
        self.assertFalse(can_request)

    def test_guest_limit(self):
        session_key = 'guest_session_123'
        guest_plan = SubscriptionPlan.objects.get(name='guest')
        
        for i in range(guest_plan.limit_count):
            prompt = Prompt.objects.create(
                session_key=session_key,
                text=f'Test prompt {i}',
                status='done'
            )
            UsageService.record_usage(None, session_key, prompt)
        
        can_request = UsageService.can_make_request(None, session_key)
        self.assertFalse(can_request)
