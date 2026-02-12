"""
Pytest configuration and shared fixtures.
"""
import pytest
from django.test import Client
from apps.subscriptions.services import SubscriptionService


@pytest.fixture
def client():
    """Returns a Django test client."""
    return Client()


@pytest.fixture
def auth_client(db, user):
    """Returns a Django test client logged in with a user."""
    client = Client()
    client.login(username=user.username, password='testpass123')
    return client


@pytest.fixture
def user(db):
    """Creates and returns a test user with profile."""
    from tests.factories import UserFactory, UserProfileFactory
    user = UserFactory()
    UserProfileFactory(user=user)
    return user


@pytest.fixture
def user_with_subscription(db, user, subscription_plans):
    """Creates a user with an active free subscription."""
    from apps.subscriptions.models import UserSubscription, SubscriptionPlan
    free_plan = SubscriptionPlan.objects.get(name='free')
    UserSubscription.objects.create(user=user, plan=free_plan, is_active=True)
    return user


@pytest.fixture
def subscription_plans(db):
    """Creates all default subscription plans."""
    SubscriptionService.get_or_create_default_plans()
    from apps.subscriptions.models import SubscriptionPlan
    return SubscriptionPlan.objects.all()


@pytest.fixture
def guest_session_key():
    """Returns a test session key for guest users."""
    return 'test_guest_session_12345678'


@pytest.fixture
def prompt(db, user):
    """Creates and returns a test prompt."""
    from tests.factories import PromptFactory
    return PromptFactory(user=user)


@pytest.fixture
def prompt_with_sections(db, prompt):
    """Creates a prompt with all section types."""
    from tests.factories import SectionFactory
    sections = []
    for section_type in ['explanation', 'summary', 'plan', 'quiz']:
        sections.append(SectionFactory(prompt=prompt, type=section_type))
    return prompt, sections
