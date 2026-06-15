from apps.analytics.models import UserEvent

class UserEventService:
    @staticmethod
    def record_event(event_type, user=None, metadata=None):
        if metadata is None:
            metadata = {}
        return UserEvent.objects.create(
            user=user,
            event_type=event_type,
            metadata=metadata
        )
