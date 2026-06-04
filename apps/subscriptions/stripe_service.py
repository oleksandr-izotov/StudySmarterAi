import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from .models import SubscriptionPlan, UserSubscription, PaymentEvent


stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:

    @classmethod
    def get_or_create_customer(cls, user: User) -> str:
        try:
            subscription = user.subscription
            if subscription.stripe_customer_id:
                return subscription.stripe_customer_id
        except UserSubscription.DoesNotExist:
            pass

        customer = stripe.Customer.create(
            email=user.email,
            name=user.get_full_name() or user.username,
            metadata={'user_id': str(user.id)}
        )

        UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                'stripe_customer_id': customer.id,
                'plan': SubscriptionPlan.objects.filter(name='free', is_active=True).first()
            }
        )

        return customer.id

    @classmethod
    def create_checkout_session(cls, user: User, plan: SubscriptionPlan, success_url: str, cancel_url: str) -> str:
        if not plan.stripe_price_id:
            raise ValueError(f"Plan {plan.name} has no Stripe price configured")

        customer_id = cls.get_or_create_customer(user)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user.id),
                'plan_name': plan.name,
            }
        )

        return session.url

    @classmethod
    def handle_checkout_completed(cls, session: dict) -> bool:
        user_id = session.get('metadata', {}).get('user_id')
        plan_name = session.get('metadata', {}).get('plan_name')
        subscription_id = session.get('subscription')
        customer_id = session.get('customer')

        if not user_id or not plan_name:
            return False

        try:
            user = User.objects.get(id=int(user_id))
            plan = SubscriptionPlan.objects.get(name=plan_name, is_active=True)
        except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
            return False

        UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': plan,
                'stripe_customer_id': customer_id,
                'stripe_subscription_id': subscription_id,
                'is_active': True,
                'expires_at': None,
            }
        )

        return True

    # Stripe subscription statuses that should keep paid access. `past_due`
    # is included on purpose: a renewal payment failed but Stripe is still
    # retrying — we keep access during that grace window rather than cutting
    # a paying customer off mid-cycle.
    ACTIVE_STATUSES = {'active', 'trialing', 'past_due'}
    # Terminal statuses that revoke paid access — drop back to the free plan.
    DOWNGRADE_STATUSES = {'canceled', 'unpaid', 'incomplete_expired'}

    @classmethod
    def _downgrade_to_free(cls, user_sub: UserSubscription) -> None:
        free_plan = SubscriptionPlan.objects.filter(name='free', is_active=True).first()
        if free_plan:
            user_sub.plan = free_plan
            user_sub.stripe_subscription_id = None
            user_sub.is_active = True
            user_sub.save()

    @classmethod
    def _find_user_sub(cls, subscription_id=None, customer_id=None):
        if subscription_id:
            sub = UserSubscription.objects.filter(stripe_subscription_id=subscription_id).first()
            if sub:
                return sub
        if customer_id:
            return UserSubscription.objects.filter(stripe_customer_id=customer_id).first()
        return None

    @classmethod
    def handle_subscription_updated(cls, subscription: dict) -> bool:
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        status = subscription.get('status')

        user_sub = cls._find_user_sub(subscription_id, customer_id)
        if user_sub is None:
            return False

        if status in cls.DOWNGRADE_STATUSES:
            # Lost access for good — move to free.
            cls._downgrade_to_free(user_sub)
        else:
            # active / trialing / past_due (grace) keep access; anything else
            # (e.g. incomplete) is treated as not-yet-active.
            user_sub.is_active = status in cls.ACTIVE_STATUSES
            user_sub.stripe_subscription_id = subscription_id
            user_sub.save()

        return True

    @classmethod
    def handle_subscription_deleted(cls, subscription: dict) -> bool:
        subscription_id = subscription.get('id')

        user_sub = UserSubscription.objects.filter(stripe_subscription_id=subscription_id).first()
        if user_sub is None:
            return False

        cls._downgrade_to_free(user_sub)
        return True

    @classmethod
    def handle_payment_failed(cls, invoice: dict) -> bool:
        """invoice.payment_failed — a renewal charge failed. Stripe also sends
        subscription.updated (status past_due) which manages the grace window,
        so here we just acknowledge and log; the user keeps access until the
        subscription transitions to a terminal status."""
        import logging
        subscription_id = invoice.get('subscription')
        customer_id = invoice.get('customer')
        user_sub = cls._find_user_sub(subscription_id, customer_id)
        if user_sub is None:
            # Nothing to do, but acknowledge so Stripe stops retrying delivery.
            return True
        logging.getLogger(__name__).warning(
            "Payment failed for subscription %s (customer %s)", subscription_id, customer_id
        )
        return True

    @classmethod
    def cancel_subscription(cls, user: User) -> bool:
        try:
            subscription = user.subscription
            if not subscription.stripe_subscription_id:
                return False

            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            return True
        except (UserSubscription.DoesNotExist, stripe.error.StripeError):
            return False

    @classmethod
    def is_event_processed(cls, event_id: str) -> bool:
        return PaymentEvent.objects.filter(event_id=event_id, processed=True).exists()

    @classmethod
    def mark_event_processed(cls, event_id: str, event_type: str, payload: dict = None):
        PaymentEvent.objects.update_or_create(
            event_id=event_id,
            defaults={
                'event_type': event_type,
                'processed': True,
                'payload': payload or {}
            }
        )

    # Map Stripe event types to their handlers. Adding a handler here is all
    # that's needed to start processing a new event type.
    EVENT_HANDLERS = {
        'checkout.session.completed': 'handle_checkout_completed',
        'customer.subscription.updated': 'handle_subscription_updated',
        'customer.subscription.deleted': 'handle_subscription_deleted',
        'invoice.payment_failed': 'handle_payment_failed',
    }

    @classmethod
    def process_event(cls, event) -> str:
        """Idempotently process a verified Stripe webhook event.

        Returns one of: 'ok' (handled now), 'duplicate' (already handled),
        'ignored' (no handler — acknowledged so Stripe stops retrying), or
        'failed' (handler could not complete — caller must return non-2xx so
        Stripe retries). The whole thing runs in one transaction with a row
        lock on the PaymentEvent so concurrent re-deliveries can't double-apply.
        """
        event_id = event['id']
        event_type = event['type']
        data_object = event['data']['object']

        with transaction.atomic():
            record, _created = (
                PaymentEvent.objects.select_for_update().get_or_create(
                    event_id=event_id,
                    defaults={
                        'event_type': event_type,
                        'processed': False,
                        'payload': data_object,
                    },
                )
            )

            if record.processed:
                return 'duplicate'

            handler_name = cls.EVENT_HANDLERS.get(event_type)
            if handler_name is None:
                # Unhandled type: ack it so Stripe doesn't keep retrying.
                record.event_type = event_type
                record.processed = True
                record.save(update_fields=['event_type', 'processed'])
                return 'ignored'

            handled_ok = getattr(cls, handler_name)(data_object)
            if not handled_ok:
                # Roll back everything (incl. this PaymentEvent row) so Stripe
                # retries the delivery later instead of us silently 200-ing.
                transaction.set_rollback(True)
                return 'failed'

            record.processed = True
            record.payload = data_object
            record.save(update_fields=['processed', 'payload'])
            return 'ok'
