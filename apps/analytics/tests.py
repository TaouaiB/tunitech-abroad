from django.test import TestCase
from apps.accounts.models import User
from .models import UserEvent
from .services.user_event import UserEventService

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class AnalyticsTests(TestCase):
    def test_user_event_service(self):
        user = create_test_user(username="analyticsuser", email="analytics@example.test", password="pw")
        
        event = UserEventService.record_event(
            event_type="test_event",
            user=user,
            metadata={"key": "value"}
        )
        
        self.assertEqual(event.event_type, "test_event")
        self.assertEqual(event.user, user)
        self.assertEqual(event.metadata["key"], "value")
        
    def test_user_event_anonymous(self):
        event = UserEventService.record_event(event_type="anon_event")
        self.assertEqual(event.event_type, "anon_event")
        self.assertIsNone(event.user)
