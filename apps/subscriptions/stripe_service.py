import stripe
from django.conf import settings
from django.contrib.auth.models import User
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

    @classmethod
    def handle_subscription_updated(cls, subscription: dict) -> bool:
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        status = subscription.get('status')

        try:
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
        except UserSubscription.DoesNotExist:
            try:
                user_sub = UserSubscription.objects.get(stripe_customer_id=customer_id)
            except UserSubscription.DoesNotExist:
                return False

        is_active = status in ['active', 'trialing']
        user_sub.is_active = is_active
        user_sub.stripe_subscription_id = subscription_id
        user_sub.save()

        return True

    @classmethod
    def handle_subscription_deleted(cls, subscription: dict) -> bool:
        subscription_id = subscription.get('id')

        try:
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
        except UserSubscription.DoesNotExist:
            return False

        free_plan = SubscriptionPlan.objects.filter(name='free', is_active=True).first()
        if free_plan:
            user_sub.plan = free_plan
            user_sub.stripe_subscription_id = None
            user_sub.is_active = True
            user_sub.save()

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
