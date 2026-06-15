from django.test import TestCase
from apps.accounts.models import User
from django.db.utils import IntegrityError
from django.db import connection
from .services.account_provisioning import AccountProvisioningService

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class UserModelTests(TestCase):
    def test_custom_user_model(self):
        self.assertEqual(User.__name__, 'User')
        self.assertEqual(User._meta.app_label, 'accounts')
    
    def test_user_creation(self):
        user = create_test_user(username="testuser", email="test@example.com", password="password123")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.public_id)

    def test_duplicate_email_rejected(self):
        create_test_user(username="u1", email="duplicate@example.com", password="password123")
        with self.assertRaises(IntegrityError):
            create_test_user(username="u2", email="duplicate@example.com", password="password456")

    def test_no_auth_user_table(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("accounts_user", tables)
        self.assertNotIn("auth_user", tables)

class AccountProvisioningServiceTests(TestCase):
    def test_idempotent_provisioning(self):
        user = create_test_user(username="provuser", email="prov@example.com", password="password123")
        
        # Test Phase 2: Creates CandidateProfile and EmailPreference idempotently
        from apps.profiles.models import CandidateProfile
        from apps.notifications.models import EmailPreference
        
        AccountProvisioningService.provision_new_user(user)
        self.assertTrue(CandidateProfile.objects.filter(user=user).exists())
        self.assertTrue(EmailPreference.objects.filter(user=user).exists())
        
        # Call again to test idempotency
        AccountProvisioningService.provision_new_user(user)
        self.assertEqual(CandidateProfile.objects.filter(user=user).count(), 1)
        self.assertEqual(EmailPreference.objects.filter(user=user).count(), 1)

class AuthViewsTests(TestCase):
    def test_login_page_status_code(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_signup_page_status_code(self):
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)
