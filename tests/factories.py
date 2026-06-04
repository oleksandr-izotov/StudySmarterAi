"""
Test factories using Factory Boy.
Provides reusable factories for creating test data.
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile, MagicLinkToken
from apps.prompts.models import Prompt, Section
from apps.subscriptions.models import SubscriptionPlan, UserSubscription, UsageLog
from django.utils import timezone
from datetime import timedelta


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Hash and PERSIST the password. (A plain PostGenerationMethodCall
        wouldn't save under skip_postgeneration_save=True, leaving the DB hash
        out of sync — which breaks client.login()/force_login session auth.)"""
        if not create:
            return
        obj.set_password(extracted or 'testpass123')
        obj.save()


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances."""
    
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    language = 'ru'
    tone = 'friendly'
    depth = 'detailed'
    format = 'bullets'
    goal = 'understand'


class SubscriptionPlanFactory(DjangoModelFactory):
    """Factory for creating SubscriptionPlan instances."""
    
    class Meta:
        model = SubscriptionPlan
    
    name = factory.Sequence(lambda n: f'plan_{n}')
    display_name = factory.LazyAttribute(lambda obj: obj.name.title())
    limit_count = 10
    limit_period = 'day'
    monthly_price = 0
    is_paid = False
    is_active = True
    sort_order = factory.Sequence(lambda n: n)


class UserSubscriptionFactory(DjangoModelFactory):
    """Factory for creating UserSubscription instances."""
    
    class Meta:
        model = UserSubscription
    
    user = factory.SubFactory(UserFactory)
    plan = factory.SubFactory(SubscriptionPlanFactory)
    is_active = True
    expires_at = None


class PromptFactory(DjangoModelFactory):
    """Factory for creating Prompt instances."""
    
    class Meta:
        model = Prompt
    
    user = factory.SubFactory(UserFactory)
    session_key = None
    text = factory.Faker('sentence', nb_words=10)
    language = 'ru'
    tone = 'friendly'
    depth = 'detailed'
    format = 'bullets'
    goal = 'understand'
    status = 'done'


class SectionFactory(DjangoModelFactory):
    """Factory for creating Section instances."""
    
    class Meta:
        model = Section
    
    prompt = factory.SubFactory(PromptFactory)
    type = 'explanation'
    content = factory.Faker('paragraph', nb_sentences=5)
    status = 'done'
    version = 1


class MagicLinkTokenFactory(DjangoModelFactory):
    """Factory for creating MagicLinkToken instances."""
    
    class Meta:
        model = MagicLinkToken
    
    email = factory.Faker('email')
    is_used = False
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=15))


class UsageLogFactory(DjangoModelFactory):
    """Factory for creating UsageLog instances."""
    
    class Meta:
        model = UsageLog
    
    user = factory.SubFactory(UserFactory)
    session_key = None
    prompt = factory.SubFactory(PromptFactory)
    action_type = 'prompt'
    cost = 1.0
