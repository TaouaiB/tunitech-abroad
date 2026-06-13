from django.test import TestCase
from apps.accounts.models import User
from .models import EmailPreference

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class EmailPreferenceTests(TestCase):
    def test_email_preference_creation(self):
        user = create_test_user(username="epuser", email="ep@example.com", password="pw")
        pref = EmailPreference.objects.create(user=user)
        
        self.assertEqual(pref.user, user)
        self.assertFalse(pref.product_updates_enabled)
        self.assertFalse(pref.weekly_digest_enabled)
        self.assertTrue(pref.cv_analysis_email_enabled)
