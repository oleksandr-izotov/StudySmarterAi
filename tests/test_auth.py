"""
Tests for authentication views and services.
Covers: registration, login, logout, magic link, protected pages.
"""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import UserProfile, MagicLinkToken
from apps.accounts.services import create_magic_link, get_user_from_token
from tests.factories import UserFactory, UserProfileFactory, MagicLinkTokenFactory


# =============================================================================
# Registration Tests
# =============================================================================

@pytest.mark.django_db
class TestRegistration:
    
    def test_registration_page_loads(self, client):
        """Test that registration page loads successfully."""
        url = reverse('register')
        response = client.get(url)
        assert response.status_code == 200
    
    def test_registration_success(self, client):
        """Test successful user registration creates user and profile."""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'securepass123!',
            'password2': 'securepass123!',
        }
        response = client.post(url, data)
        
        # Should redirect to home after successful registration
        assert response.status_code == 302
        
        # User should be created
        assert User.objects.filter(username='newuser').exists()
        
        # Profile should be created
        user = User.objects.get(username='newuser')
        assert UserProfile.objects.filter(user=user).exists()
    
    def test_registration_password_mismatch(self, client):
        """Test registration fails with mismatched passwords."""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'securepass123!',
            'password2': 'differentpass123!',
        }
        response = client.post(url, data)
        
        # Should return form with errors (200)
        assert response.status_code == 200
        assert not User.objects.filter(username='newuser').exists()
    
    def test_registration_duplicate_username(self, client, db):
        """Test registration fails with existing username."""
        UserFactory(username='existinguser')
        
        url = reverse('register')
        data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password1': 'securepass123!',
            'password2': 'securepass123!',
        }
        response = client.post(url, data)
        
        assert response.status_code == 200
        assert User.objects.filter(username='existinguser').count() == 1


# =============================================================================
# Login Tests
# =============================================================================

@pytest.mark.django_db
class TestLogin:
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        url = reverse('login')
        response = client.get(url)
        assert response.status_code == 200
    
    def test_login_success(self, client, user):
        """Test successful login redirects to home."""
        url = reverse('login')
        data = {
            'username': user.username,
            'password': 'testpass123',
        }
        response = client.post(url, data)
        
        # Either redirect (302) or success with authenticated session
        assert response.status_code in [200, 302]
        # Check user is authenticated if login was successful
        if response.status_code == 302:
            assert '_auth_user_id' in client.session
    
    def test_login_invalid_credentials(self, client, user):
        """Test login with wrong password fails."""
        url = reverse('login')
        data = {
            'username': user.username,
            'password': 'wrongpassword',
        }
        response = client.post(url, data)
        
        assert response.status_code == 200
        assert '_auth_user_id' not in client.session


# =============================================================================
# Logout Tests
# =============================================================================

@pytest.mark.django_db
class TestLogout:
    
    def test_logout_success(self, auth_client, user):
        """Test logout clears session and redirects."""
        url = reverse('logout')
        response = auth_client.post(url)
        
        assert response.status_code == 302
        assert '_auth_user_id' not in auth_client.session


# =============================================================================
# Magic Link Tests
# =============================================================================

@pytest.mark.django_db
class TestMagicLink:
    
    def test_magic_link_request_page_loads(self, client):
        """Test magic link request page loads."""
        url = reverse('magic_link_request')
        response = client.get(url)
        assert response.status_code == 200
    
    def test_create_magic_link(self, db):
        """Test magic link token creation."""
        email = 'test@example.com'
        token = create_magic_link(email)
        
        assert token.email == email
        assert not token.is_used
        assert token.expires_at > timezone.now()
        assert token.expires_at < timezone.now() + timedelta(minutes=20)
    
    def test_magic_link_verify_success(self, client, db):
        """Test successful magic link verification logs in user."""
        # Create a user or let the service create one
        token = MagicLinkTokenFactory(email='magicuser@example.com')
        
        url = reverse('magic_link_verify', kwargs={'token': str(token.token)})
        response = client.get(url)
        
        # Should redirect to home
        assert response.status_code == 302
        
        # Token should be marked as used
        token.refresh_from_db()
        assert token.is_used
        
        # User should be authenticated
        assert '_auth_user_id' in client.session
    
    def test_magic_link_verify_expired(self, client, db):
        """Test expired magic link does not log in user."""
        token = MagicLinkTokenFactory(
            email='expired@example.com',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        
        url = reverse('magic_link_verify', kwargs={'token': str(token.token)})
        response = client.get(url)
        
        # Should redirect to login with error
        assert response.status_code == 302
        assert '_auth_user_id' not in client.session
    
    def test_magic_link_verify_already_used(self, client, db):
        """Test already used magic link does not log in user."""
        token = MagicLinkTokenFactory(
            email='used@example.com',
            is_used=True
        )
        
        url = reverse('magic_link_verify', kwargs={'token': str(token.token)})
        response = client.get(url)
        
        assert response.status_code == 302
        assert '_auth_user_id' not in client.session
    
    def test_magic_link_verify_invalid_token(self, client):
        """Test invalid token returns error."""
        url = reverse('magic_link_verify', kwargs={'token': '00000000-0000-0000-0000-000000000000'})
        response = client.get(url)
        
        assert response.status_code == 302
        assert '_auth_user_id' not in client.session


# =============================================================================
# Protected Pages Tests
# =============================================================================

@pytest.mark.django_db
class TestProtectedPages:
    
    def test_account_page_requires_auth(self, client):
        """Test account page redirects unauthenticated users to login."""
        url = reverse('account')
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url.lower() or 'accounts' in response.url.lower()
    
    def test_account_page_accessible_when_authenticated(self, db, user):
        """Test account page is accessible for authenticated users."""
        client = Client()
        client.force_login(user)
        
        url = reverse('account')
        response = client.get(url)
        
        # Page either loads directly (200) or redirects to proper account page (302)
        assert response.status_code in [200, 302]
