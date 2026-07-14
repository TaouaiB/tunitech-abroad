import hashlib
from contextlib import contextmanager

from allauth.account.models import EmailAddress
from django.core.exceptions import ValidationError
from django.db import connection, transaction

from apps.accounts.models import User


class EmailIdentityService:
    ERROR_MESSAGE = "Cette adresse email ne peut pas être utilisée."

    @staticmethod
    def normalize(email: str) -> str:
        return (email or "").strip().lower()

    @classmethod
    def advisory_lock_key(cls, email: str) -> int:
        """Return a stable signed bigint accepted by pg_advisory_xact_lock."""
        digest = hashlib.sha256(cls.normalize(email).encode("utf-8")).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=True)

    @classmethod
    def _acquire_advisory_lock(cls, normalized_email: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [cls.advisory_lock_key(normalized_email)])

    @classmethod
    def validate_available(cls, email: str, *, current_user) -> str:
        normalized = cls.normalize(email)
        if not normalized:
            raise ValidationError(cls.ERROR_MESSAGE)

        other_users = User.objects.filter(email__iexact=normalized)
        other_addresses = EmailAddress.objects.filter(email__iexact=normalized)
        if current_user and current_user.pk:
            other_users = other_users.exclude(pk=current_user.pk)
            other_addresses = other_addresses.exclude(user_id=current_user.pk)

        if other_users.exists() or other_addresses.exists():
            raise ValidationError(cls.ERROR_MESSAGE)
        return normalized

    @classmethod
    @contextmanager
    def locked_available_identity(cls, email: str, *, current_user):
        """Serialize ownership decisions for one canonical email until commit."""
        normalized = cls.normalize(email)
        if not normalized:
            raise ValidationError(cls.ERROR_MESSAGE)
        with transaction.atomic():
            cls._acquire_advisory_lock(normalized)
            cls.validate_available(normalized, current_user=current_user)
            yield normalized
