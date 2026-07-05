from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.core.context_processors import email_verification_banner

User = get_user_model()


class UIHeaderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test", email="test@example.com")

    def test_logged_out_header(self):
        template = Template('{% extends "base.html" %}{% block content %}{% endblock %}')
        context = Context({"user": AnonymousUser()})
        rendered = template.render(context)

        self.assertIn("Offres", rendered)
        self.assertIn("Recommandations", rendered)
        self.assertIn('href="/about/">À propos</a>', rendered)
        self.assertIn("Connexion", rendered)
        self.assertIn("next=/dashboard/recommendations/", rendered)
        self.assertNotIn("Favoris", rendered)
        self.assertNotIn("Profil</a>", rendered)
        self.assertNotIn("Paramètres", rendered)
        self.assertNotIn("Déconnexion", rendered)
        self.assertNotIn("Tableau de bord", rendered)

    def test_logged_in_header(self):
        template = Template('{% extends "base.html" %}{% block content %}{% endblock %}')
        context = Context({"user": self.user})
        rendered = template.render(context)

        self.assertIn("Offres", rendered)
        self.assertIn("Recommandations", rendered)
        self.assertIn("Favoris", rendered)
        self.assertIn("Profil", rendered)
        self.assertIn("Paramètres", rendered)
        self.assertIn('href="/about/">À propos</a>', rendered)
        self.assertIn("Déconnexion", rendered)
        self.assertNotIn("Tableau de bord", rendered)


class UIMessagesTests(TestCase):
    def test_toast_messages_present_in_base_template(self):
        class MockMessage:
            def __init__(self, message, tags):
                self.message = message
                self.tags = tags

            def __str__(self):
                return self.message

        messages = [
            MockMessage("Test success toast", "success"),
            MockMessage("Test error toast", "error"),
        ]

        template = Template(
            """
        {% extends "base.html" %}
        {% block content %}Test{% endblock %}
        """
        )

        context = Context(
            {
                "messages": messages,
                "user": AnonymousUser(),
            }
        )

        rendered = template.render(context)

        self.assertIn("toast-wrap", rendered)
        self.assertIn("data-django-toast", rendered)
        self.assertIn("Test success toast", rendered)
        self.assertIn("Test error toast", rendered)
        self.assertIn("good", rendered)
        self.assertIn("bad", rendered)


class AboutModalTests(TestCase):
    def test_privacy_and_terms_modals_are_overlay_dialogs(self):
        response = self.client.get(reverse("core:about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-modal-open="privacy-modal"', html=False)
        self.assertContains(response, 'data-modal-open="terms-modal"', html=False)
        self.assertContains(response, 'class="modal-backdrop" id="privacy-modal" data-modal="privacy-modal" hidden', html=False)
        self.assertContains(response, 'class="modal-backdrop" id="terms-modal" data-modal="terms-modal" hidden', html=False)
        self.assertContains(response, 'role="dialog"', html=False)
        self.assertContains(response, 'aria-modal="true"', html=False)
        self.assertContains(response, 'data-modal-close', html=False)
        self.assertContains(response, 'data-en="Privacy"', html=False)
        self.assertContains(response, 'data-en="Terms"', html=False)
        self.assertContains(response, "CV files stay private and are not publicly exposed.")
        self.assertContains(response, "Matching scores and recommendations are guidance only.")
        self.assertNotContains(response, "onclick=\"var m=document.getElementById")


class EmailBannerContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create(username="banneruser", email="banner@example.com")

    def test_anonymous_user(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()

        context = email_verification_banner(request)

        self.assertFalse(context["show_email_verification_banner"])

    def test_authenticated_unverified_user(self):
        request = self.factory.get("/")
        request.user = self.user

        context = email_verification_banner(request)

        self.assertTrue(context["show_email_verification_banner"])

    def test_authenticated_verified_user(self):
        EmailAddress.objects.create(
            user=self.user,
            email="banner@example.com",
            primary=True,
            verified=True,
        )
        request = self.factory.get("/")
        request.user = self.user

        context = email_verification_banner(request)

        self.assertFalse(context["show_email_verification_banner"])
