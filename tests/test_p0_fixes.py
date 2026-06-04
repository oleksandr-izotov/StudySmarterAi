"""Tests for the P0 production-readiness fixes:
  - Stripe webhook idempotency + return-value handling (StripeService.process_event)
  - Atomic usage quota consume (UsageService.try_consume)
Magic-link single-use atomicity is already covered by tests/test_auth.py.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from apps.subscriptions.models import SubscriptionPlan, UserSubscription, UsageLog, PaymentEvent
from apps.subscriptions.services import SubscriptionService, UsageService
from apps.subscriptions.stripe_service import StripeService


def _checkout_event(event_id, user_id, plan_name='pro'):
    return {
        'id': event_id,
        'type': 'checkout.session.completed',
        'data': {'object': {
            'metadata': {'user_id': str(user_id), 'plan_name': plan_name},
            'subscription': 'sub_test_123',
            'customer': 'cus_test_123',
        }},
    }


class StripeWebhookProcessEventTests(TestCase):
    def setUp(self):
        SubscriptionService.get_or_create_default_plans()
        self.user = User.objects.create_user(username='payer', password='x')

    def test_successful_event_is_processed_and_upgrades_plan(self):
        result = StripeService.process_event(_checkout_event('evt_ok', self.user.id))
        self.assertEqual(result, 'ok')
        self.assertTrue(PaymentEvent.objects.filter(event_id='evt_ok', processed=True).exists())
        self.user.subscription.refresh_from_db()
        self.assertEqual(self.user.subscription.plan.name, 'pro')
        self.assertTrue(self.user.subscription.is_active)

    def test_duplicate_event_is_not_processed_twice(self):
        StripeService.process_event(_checkout_event('evt_dup', self.user.id))
        result = StripeService.process_event(_checkout_event('evt_dup', self.user.id))
        self.assertEqual(result, 'duplicate')
        self.assertEqual(PaymentEvent.objects.filter(event_id='evt_dup').count(), 1)

    def test_failed_handler_does_not_mark_processed_and_rolls_back(self):
        # No metadata -> handle_checkout_completed returns False -> 'failed',
        # and the PaymentEvent row must be rolled back so Stripe can retry.
        bad = {'id': 'evt_fail', 'type': 'checkout.session.completed',
               'data': {'object': {'metadata': {}}}}
        result = StripeService.process_event(bad)
        self.assertEqual(result, 'failed')
        self.assertFalse(PaymentEvent.objects.filter(event_id='evt_fail').exists())

    def test_unknown_event_type_is_acknowledged(self):
        evt = {'id': 'evt_unknown', 'type': 'invoice.paid', 'data': {'object': {}}}
        result = StripeService.process_event(evt)
        self.assertEqual(result, 'ignored')
        self.assertTrue(PaymentEvent.objects.filter(event_id='evt_unknown', processed=True).exists())


class StripeSubscriptionStatusTests(TestCase):
    def setUp(self):
        SubscriptionService.get_or_create_default_plans()
        self.user = User.objects.create_user(username='sub', password='x')
        StripeService.process_event(_checkout_event('evt_setup', self.user.id))
        self.user.subscription.refresh_from_db()

    def _updated_event(self, status, eid):
        return {'id': eid, 'type': 'customer.subscription.updated',
                'data': {'object': {'id': 'sub_test_123', 'customer': 'cus_test_123', 'status': status}}}

    def test_past_due_keeps_access_grace(self):
        StripeService.process_event(self._updated_event('past_due', 'evt_pastdue'))
        self.user.subscription.refresh_from_db()
        self.assertTrue(self.user.subscription.is_active)
        self.assertEqual(self.user.subscription.plan.name, 'pro')

    def test_canceled_downgrades_to_free(self):
        StripeService.process_event(self._updated_event('canceled', 'evt_canceled'))
        self.user.subscription.refresh_from_db()
        self.assertEqual(self.user.subscription.plan.name, 'free')

    def test_payment_failed_is_acknowledged(self):
        evt = {'id': 'evt_payfail', 'type': 'invoice.payment_failed',
               'data': {'object': {'subscription': 'sub_test_123', 'customer': 'cus_test_123'}}}
        self.assertEqual(StripeService.process_event(evt), 'ok')


class TryConsumeQuotaTests(TestCase):
    def setUp(self):
        SubscriptionService.get_or_create_default_plans()
        self.user = User.objects.create_user(username='student', password='x')  # free plan: 10/week

    def test_consume_records_usage_and_blocks_over_limit(self):
        limit = SubscriptionPlan.objects.get(name='free').limit_count
        for i in range(limit):
            self.assertTrue(
                UsageService.try_consume(self.user, None, prompt=None),
                msg=f'request {i + 1} should be allowed',
            )
        # Over the limit now
        self.assertFalse(UsageService.try_consume(self.user, None, prompt=None))
        # Exactly `limit` usage rows recorded — the blocked request did NOT record
        self.assertEqual(UsageLog.objects.filter(user=self.user).count(), limit)

    def test_blocked_consume_records_nothing(self):
        plan = SubscriptionPlan.objects.get(name='free')
        # Pre-fill to the limit
        for _ in range(plan.limit_count):
            UsageService.record_usage(self.user, None, None, cost=Decimal('1.0'))
        self.assertFalse(UsageService.try_consume(self.user, None, prompt=None))
        self.assertEqual(UsageLog.objects.filter(user=self.user).count(), plan.limit_count)
