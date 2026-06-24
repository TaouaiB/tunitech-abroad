from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class HomeCTATests(TestCase):
    def test_anonymous_homepage_shows_signup_cta(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Créer un compte")
        self.assertContains(response, "créez un compte")
        self.assertNotContains(response, "Aller au tableau de bord")
        self.assertNotContains(response, "Voir mes recommandations")
        self.assertNotContains(response, "Gérer mon CV")

    def test_authenticated_homepage_shows_candidate_ctas(self):
        user = get_user_model().objects.create_user(
            username="candidate",
            email="candidate@example.test",
            password="pass",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Créer un compte")
        self.assertNotContains(response, "créez un compte")
        self.assertContains(response, "Aller au tableau de bord")
        self.assertContains(response, "Voir mes recommandations")
        self.assertContains(response, "Gérer mon CV")
