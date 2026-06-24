from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from apps.cvs.models import CVUpload
from django.core.files.uploadedfile import SimpleUploadedFile

UserModel = get_user_model()


def create_test_user(
    *,
    username: str,
    email: str,
    password: str = "pw",
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


class CVViewTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="testuser3", email="view@test.com", password="password")
        self.client = Client()

    def test_dashboard_cv_requires_login(self):
        response = self.client.get(reverse('dashboard:cv'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_cv_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:cv'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_cv_upload_dropzone_is_clickable_and_valid(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:cv'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'method="post"')
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'name="file"')
        self.assertContains(response, 'id="id_file"')
        self.assertContains(response, 'for="id_file"')
        self.assertContains(response, 'role="button"')
        self.assertContains(response, 'tabindex="0"')
        self.assertContains(response, '@drop.prevent="handleDrop($event)"')
        self.assertContains(response, 'name="consent_accepted"')

    def test_dashboard_cv_status_requires_owner(self):
        other_user = create_test_user(username="otheruser", email="other@test.com", password="password")
        file = SimpleUploadedFile("test.pdf", b"pdf_content", content_type="application/pdf")
        cv = CVUpload.objects.create(
            user=other_user, file=file, original_filename="test.pdf",
            file_hash="hash", file_size=1, is_active=True
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:cv_status', args=[cv.public_id]))
        self.assertEqual(response.status_code, 404)

    def test_dashboard_cv_uses_alpine_modal(self):
        file = SimpleUploadedFile("test.pdf", b"pdf_content", content_type="application/pdf")
        cv = CVUpload.objects.create(
            user=self.user, file=file, original_filename="test.pdf",
            file_hash="hash", file_size=1, is_active=True
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:cv'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "confirm" + "(")
        self.assertContains(response, "x-show=\"showDeleteModal\"")
        self.assertContains(response, "Supprimer ce CV ?")
        self.assertContains(response, "name=\"delete_cv_id\"")
        self.assertContains(response, f'value="{cv.public_id}"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(response, f'value="{cv.id}"')
