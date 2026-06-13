from django.test import TestCase
from apps.accounts.models import User
from django.db.utils import IntegrityError
from django.db import connection
from .services.account_provisioning import AccountProvisioningService

class UserModelTests(TestCase):
    def test_custom_user_model(self):
        self.assertEqual(User.__name__, 'User')
        self.assertEqual(User._meta.app_label, 'accounts')
    
    def test_user_creation(self):
        user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.public_id)

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username="u1", email="duplicate@example.com", password="password123")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(username="u2", email="duplicate@example.com", password="password456")

    def test_no_auth_user_table(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("accounts_user", tables)
        self.assertNotIn("auth_user", tables)

class AccountProvisioningServiceTests(TestCase):
    def test_idempotent_provisioning(self):
        user = User.objects.create_user(username="provuser", email="prov@example.com", password="password123")
        
        # Test Phase 1 boundary (no real profiles created, just safe to call multiple times)
        try:
            AccountProvisioningService.provision_new_user(user)
            AccountProvisioningService.provision_new_user(user)
            success = True
        except Exception:
            success = False
            
        self.assertTrue(success)

class AuthViewsTests(TestCase):
    def test_login_page_status_code(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_signup_page_status_code(self):
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)
