from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from django.urls import reverse

class SettingsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings_url = reverse('settings:index')
        
        # Create test user
        self.user = User.objects.create_user(username='testuser', password='password')
        # Profile is created via signal or manually if signal not exists (we assumed manual in views for now)
        # But let's create it manually to be sure for this test context if signals aren't active
        self.profile = UserProfile.objects.create(user=self.user)

    def test_guest_settings_save_to_session(self):
        """Test that settings are saved to session for guest users"""
        response = self.client.post(self.settings_url, {
            'language': 'en',
            'tone': 'strict',
            'depth': 'short'
        })
        
        self.assertEqual(response.status_code, 302) # Redirects
        self.assertEqual(self.client.session['language'], 'en')
        self.assertEqual(self.client.session['tone'], 'strict')
        self.assertEqual(self.client.session['depth'], 'short')

    def test_auth_user_settings_save_to_db(self):
        """Test that settings are saved to UserProfile for auth users"""
        self.client.login(username='testuser', password='password')
        
        response = self.client.post(self.settings_url, {
            'language': 'de',
            'tone': 'strict',
            'depth': 'short'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Refresh profile from DB
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.language, 'de')
        self.assertEqual(self.profile.tone, 'strict')
        self.assertEqual(self.profile.depth, 'short')
        
        # Check session sync (optional but good for consistency)
        self.assertEqual(self.client.session['language'], 'de')

    def test_default_settings(self):
        """Test default values for new session"""
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['settings']['language'], 'ru')
