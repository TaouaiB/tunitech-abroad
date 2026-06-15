from django.test import TestCase
from apps.accounts.models import User
from .models import ConsentRecord
from .services.consent import ConsentService

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class ConsentTests(TestCase):
    def test_consent_service_records(self):
        user = create_test_user(username="consentuser", email="consent@example.com", password="pw")
        
        record = ConsentService.record_consent(
            user=user,
            consent_type="terms",
            consent_version="v1.0",
            accepted=True,
            ip_address="127.0.0.1",
            user_agent="TestAgent"
        )
        
        self.assertEqual(record.user, user)
        self.assertEqual(record.consent_type, "terms")
        self.assertEqual(record.consent_version, "v1.0")
        self.assertTrue(record.accepted)
        self.assertEqual(record.ip_address, "127.0.0.1")
        self.assertEqual(record.user_agent, "TestAgent")
