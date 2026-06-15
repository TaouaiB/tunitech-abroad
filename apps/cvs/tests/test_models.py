from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.cvs.models import CVUpload, CVParsedData

UserModel = get_user_model()


def create_test_user(
    *,
    username: str,
    email: str,
    password: str = "password",
    is_staff: bool = False,
) -> AbstractBaseUser:
    user = UserModel.objects.create(
        username=username,
        email=email,
        is_staff=is_staff,
    )
    user.set_password(password)
    user.save(update_fields=["password"])
    return user

class CVModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="testuser", email="test@test.com", password="password")
        self.file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")

    def test_soft_delete(self):
        cv = CVUpload.objects.create(
            user=self.user,
            file=self.file,
            original_filename="test.pdf",
            file_hash="testhash",
            file_size=12,
            is_active=True
        )
        self.assertEqual(CVUpload.objects.count(), 1)
        cv.soft_delete()
        self.assertEqual(CVUpload.objects.count(), 0)
        self.assertEqual(CVUpload.all_objects.count(), 1)
        cv.refresh_from_db()
        self.assertFalse(cv.is_active)
        self.assertIsNotNone(cv.deleted_at)
        self.assertEqual(cv.parse_status, 'deleted')

    def test_one_active_cv_per_user(self):
        CVUpload.objects.create(
            user=self.user, file=self.file, original_filename="1.pdf",
            file_hash="hash1", file_size=1, is_active=True
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CVUpload.objects.create(
                user=self.user, file=self.file, original_filename="2.pdf",
                file_hash="hash2", file_size=2, is_active=True
            )

    def test_cv_parsed_data_one_to_one(self):
        cv = CVUpload.objects.create(
            user=self.user, file=self.file, original_filename="1.pdf",
            file_hash="hash1", file_size=1, is_active=True
        )
        parsed = CVParsedData.objects.create(cv_upload=cv, raw_text="hello")
        self.assertEqual(CVParsedData.objects.get(cv_upload=cv), parsed)

    def test_cv_file_has_no_public_url(self):
        cv = CVUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
            original_filename="cv.pdf",
            file_hash="hash-private-url",
            file_size=12,
            is_active=True,
        )

        with self.assertRaises(ValueError):
            _ = cv.file.url
