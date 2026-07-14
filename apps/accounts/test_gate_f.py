import threading
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.db import IntegrityError, close_old_connections
from django.test import Client, RequestFactory, TestCase, TransactionTestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.services.email_identity import EmailIdentityService
from apps.accounts.services.user_identity import UserIdentityService
from apps.accounts.signals import populate_profile_from_social_data
from apps.accounts.services.account_provisioning import AccountProvisioningService
from apps.profiles.forms import ProfileForm


class GateFNameOwnershipTests(TestCase):
    def test_settings_edit_persists_names_and_profile_has_no_name_editor(self):
        user = User.objects.create_user(username="name-owner", email="name-owner@example.test", password="pass")
        AccountProvisioningService.provision_new_user(user)
        self.client.force_login(user)

        response = self.client.post(
            reverse("dashboard:account"),
            {"account_action": "update_names", "first_name": "Amina", "last_name": "Ben Ali"},
        )
        self.assertRedirects(response, reverse("dashboard:account"), fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertEqual((user.first_name, user.last_name), ("Amina", "Ben Ali"))
        self.assertNotIn("full_name", ProfileForm().fields)
        profile_response = self.client.get(reverse("dashboard:profile"))
        self.assertNotContains(profile_response, 'name="full_name"', html=False)

    def test_social_names_fill_blanks_only_and_missing_name_is_safe(self):
        user = User.objects.create_user(username="oauth-names", email="oauth-names@example.test")
        AccountProvisioningService.provision_new_user(user)
        sociallogin = type("Login", (), {"account": type("Account", (), {
            "provider": "google",
            "extra_data": {"given_name": "Initial", "family_name": "Provider"},
        })()})()
        populate_profile_from_social_data(user, sociallogin)
        user.refresh_from_db()
        self.assertEqual((user.first_name, user.last_name), ("Initial", "Provider"))

        UserIdentityService.update_names(user, first_name="Edited", last_name="Locally")
        sociallogin.account.extra_data = {"given_name": "Changed", "family_name": "Provider"}
        populate_profile_from_social_data(user, sociallogin)
        user.refresh_from_db()
        self.assertEqual((user.first_name, user.last_name), ("Edited", "Locally"))

        blank_user = User.objects.create_user(username="oauth-no-name", email="oauth-no-name@example.test")
        AccountProvisioningService.provision_new_user(blank_user)
        sociallogin.account.extra_data = {"email": blank_user.email}
        populate_profile_from_social_data(blank_user, sociallogin)
        blank_user.refresh_from_db()
        self.assertEqual((blank_user.first_name, blank_user.last_name), ("", ""))

    def test_social_provisioning_leaves_legacy_name_untouched_and_user_name_wins(self):
        user = User.objects.create_user(username="legacy-name", email="legacy-name@example.test")
        profile = AccountProvisioningService.provision_new_user(user)
        profile.full_name = "Ancien Nom"
        profile.save(update_fields=["full_name"])
        sociallogin = type("Login", (), {"account": type("Account", (), {
            "provider": "google",
            "extra_data": {"given_name": "Nouveau", "family_name": "Nom", "name": "Provider Name"},
        })()})()

        populate_profile_from_social_data(user, sociallogin)
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertEqual(user.get_full_name(), "Nouveau Nom")
        self.assertEqual(profile.full_name, "Ancien Nom")

        legacy_user = User.objects.create_user(username="legacy-only", email="legacy-only@example.test")
        legacy_profile = AccountProvisioningService.provision_new_user(legacy_user)
        legacy_profile.full_name = "Nom Hérité"
        legacy_profile.save(update_fields=["full_name"])
        from apps.dashboard.views import dashboard_home

        legacy_request = RequestFactory().get("/dashboard/")
        legacy_request.user = legacy_user
        self.assertContains(dashboard_home(legacy_request), "Nom Hérité")

        UserIdentityService.update_names(user, first_name="Édité", last_name="Localement")
        request = RequestFactory().get("/dashboard/")
        request.user = user
        response = dashboard_home(request)
        self.assertContains(response, "Édité Localement")
        self.assertNotContains(response, "Ancien Nom")


class GateFEmailIdentityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="email-current", email="current@example.test", password="pass")
        self.primary = EmailAddress.objects.create(user=self.user, email=self.user.email, primary=True, verified=False)
        self.other = User.objects.create_user(username="email-other", email="other@example.test", password="pass")
        EmailAddress.objects.create(user=self.other, email=self.other.email, primary=True, verified=True)
        EmailAddress.objects.create(user=self.other, email="secondary@example.test", primary=False, verified=False)
        self.client.force_login(self.user)

    def add_email(self, email):
        return self.client.post(reverse("account_email"), {"action_add": "1", "email": email})

    def test_other_canonical_secondary_and_case_variants_are_rejected_inline(self):
        for email in ("OTHER@example.test", "Secondary@Example.Test"):
            with self.subTest(email=email):
                response = self.add_email(email)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Cette adresse email ne peut pas être utilisée.")
                self.assertFalse(EmailAddress.objects.filter(user=self.user, email__iexact=email).exists())

    def test_own_records_are_allowed_for_primary_validation_and_primary_syncs_user(self):
        secondary = EmailAddress.objects.create(
            user=self.user, email="mine-secondary@example.test", primary=False, verified=True
        )
        response = self.client.post(
            reverse("account_email"), {"email": secondary.email, "action_primary": "1"}
        )
        self.assertRedirects(response, reverse("account_email"), fetch_redirect_response=False)
        self.user.refresh_from_db()
        secondary.refresh_from_db()
        self.assertTrue(secondary.primary)
        self.assertEqual(self.user.email, secondary.email)

    def test_another_users_selected_email_cannot_be_promoted(self):
        response = self.client.post(
            reverse("account_email"), {"email": self.other.email, "action_primary": "1"}
        )
        self.assertRedirects(response, reverse("account_email"), fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.primary.refresh_from_db()
        self.assertEqual(self.user.email, "current@example.test")
        self.assertTrue(self.primary.primary)

    def test_constraint_fallback_is_form_error_not_500(self):
        with patch("allauth.account.views.EmailView.form_valid", side_effect=IntegrityError("race")):
            response = self.add_email("race@example.test")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cette adresse email ne peut pas être utilisée.")

    def test_banner_uses_primary_verification_only(self):
        secondary = EmailAddress.objects.create(
            user=self.user, email="verified-secondary@example.test", primary=False, verified=True
        )
        response = self.client.get(reverse("jobs:list"))
        self.assertTrue(response.context["show_email_verification_banner"])

        self.primary.verified = True
        self.primary.save(update_fields=["verified"])
        response = self.client.get(reverse("jobs:list"))
        self.assertFalse(response.context["show_email_verification_banner"])
        secondary.refresh_from_db()
        self.assertTrue(secondary.verified)

    def test_confirmation_token_verifies_only_its_exact_address_and_owner(self):
        confirmation = self.primary.send_confirmation()
        other_primary = EmailAddress.objects.get(user=self.other, primary=True)
        self.client.force_login(self.other)
        response = self.client.post(reverse("account_confirm_email", args=[confirmation.key]))
        self.assertIn(response.status_code, (200, 302))
        self.primary.refresh_from_db()
        other_primary.refresh_from_db()
        self.assertTrue(self.primary.verified)
        self.assertTrue(other_primary.verified)
        self.assertEqual(self.primary.user_id, self.user.id)

    def test_secondary_confirmation_does_not_verify_primary(self):
        secondary = EmailAddress.objects.create(
            user=self.user, email="confirm-secondary@example.test", primary=False, verified=False
        )
        confirmation = secondary.send_confirmation()
        response = self.client.post(reverse("account_confirm_email", args=[confirmation.key]))
        self.assertIn(response.status_code, (200, 302))
        secondary.refresh_from_db()
        self.primary.refresh_from_db()
        self.assertTrue(secondary.verified)
        self.assertFalse(self.primary.verified)

    def test_email_page_actions_and_responsive_markup_match_record_state(self):
        EmailAddress.objects.create(user=self.user, email="verified@example.test", verified=True, primary=False)
        EmailAddress.objects.create(
            user=self.user,
            email="a-very-long-unverified-address-for-mobile-layout@example.test",
            verified=False,
            primary=False,
        )
        response = self.client.get(reverse("account_email"))
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        primary_form = html.split(f'value="{self.primary.email}"', 1)[1].split("</form>", 1)[0]
        self.assertIn("Primary", primary_form)
        self.assertIn('data-fr="Principale" data-en="Primary"', primary_form)
        self.assertIn(">Principale</span>", primary_form)
        self.assertNotIn("action_primary", primary_form)
        verified_form = html.split('value="verified@example.test"', 1)[1].split("</form>", 1)[0]
        self.assertNotIn("action_send", verified_form)
        unverified_form = html.split('value="a-very-long-unverified-address-for-mobile-layout@example.test"', 1)[1].split("</form>", 1)[0]
        self.assertIn("action_send", unverified_form)
        self.assertIn("flex-wrap:wrap", html)
        self.assertIn("overflow-wrap:anywhere", html)

    def test_name_fields_use_specific_autocomplete_tokens(self):
        from apps.accounts.forms import AccountNameForm

        form = AccountNameForm(user=self.user)
        self.assertEqual(form.fields["first_name"].widget.attrs["autocomplete"], "given-name")
        self.assertEqual(form.fields["last_name"].widget.attrs["autocomplete"], "family-name")


class GateFEmailIdentityConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.first = User.objects.create_user(
            username="race-first", email="race-first@example.test", password="pass"
        )
        self.second = User.objects.create_user(
            username="race-second", email="race-second@example.test", password="pass"
        )
        EmailAddress.objects.create(user=self.first, email=self.first.email, primary=True, verified=True)
        EmailAddress.objects.create(user=self.second, email=self.second.email, primary=True, verified=True)

    def test_concurrent_case_variant_adds_have_one_owner_and_normal_loser_response(self):
        clients = [Client(), Client()]
        clients[0].force_login(self.first)
        clients[1].force_login(self.second)
        barrier = threading.Barrier(2)
        original_lock = EmailIdentityService._acquire_advisory_lock
        results = [None, None]

        def synchronized_lock(email):
            barrier.wait(timeout=10)
            return original_lock(email)

        def submit(index, email):
            close_old_connections()
            try:
                results[index] = clients[index].post(
                    reverse("account_email"), {"action_add": "1", "email": email}
                )
            finally:
                close_old_connections()

        with patch.object(EmailIdentityService, "_acquire_advisory_lock", side_effect=synchronized_lock):
            threads = [
                threading.Thread(target=submit, args=(0, "Shared.Race@Example.Test")),
                threading.Thread(target=submit, args=(1, "shared.race@example.test")),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=15)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        owners = EmailAddress.objects.filter(email__iexact="shared.race@example.test")
        self.assertEqual(owners.count(), 1)
        self.assertEqual(sorted(response.status_code for response in results), [200, 302])
        loser = next(response for response in results if response.status_code == 200)
        self.assertContains(loser, EmailIdentityService.ERROR_MESSAGE)
        self.assertEqual(
            EmailIdentityService.advisory_lock_key("Shared.Race@Example.Test"),
            EmailIdentityService.advisory_lock_key("shared.race@example.test"),
        )

        owner = owners.get().user
        with EmailIdentityService.locked_available_identity("SHARED.RACE@example.test", current_user=owner):
            pass

    def test_primary_promotion_revalidates_under_lock_and_same_user_promotion_works(self):
        secondary = EmailAddress.objects.create(
            user=self.first, email="promote@example.test", primary=False, verified=True
        )
        client = Client()
        client.force_login(self.first)
        with patch.object(
            EmailIdentityService,
            "_acquire_advisory_lock",
            wraps=EmailIdentityService._acquire_advisory_lock,
        ) as lock:
            response = client.post(
                reverse("account_email"), {"email": secondary.email, "action_primary": "1"}
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(lock.called)
        secondary.refresh_from_db()
        self.first.refresh_from_db()
        self.assertTrue(secondary.primary)
        self.assertEqual(self.first.email, secondary.email)

    def test_concurrent_primary_promotion_and_other_account_claim_do_not_race(self):
        secondary = EmailAddress.objects.create(
            user=self.first, email="promotion-race@example.test", primary=False, verified=True
        )
        clients = [Client(), Client()]
        clients[0].force_login(self.first)
        clients[1].force_login(self.second)
        start = threading.Barrier(2)
        results = [None, None]

        def promote():
            close_old_connections()
            try:
                start.wait(timeout=10)
                results[0] = clients[0].post(
                    reverse("account_email"),
                    {"email": secondary.email, "action_primary": "1"},
                )
            finally:
                close_old_connections()

        def claim():
            close_old_connections()
            try:
                start.wait(timeout=10)
                results[1] = clients[1].post(
                    reverse("account_email"),
                    {"email": "PROMOTION-RACE@example.test", "action_add": "1"},
                )
            finally:
                close_old_connections()

        threads = [threading.Thread(target=promote), threading.Thread(target=claim)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(results[0].status_code, 302)
        self.assertEqual(results[1].status_code, 200)
        self.assertContains(results[1], EmailIdentityService.ERROR_MESSAGE)
        self.assertEqual(EmailAddress.objects.filter(email__iexact=secondary.email).count(), 1)
        secondary.refresh_from_db()
        self.assertTrue(secondary.primary)


class GateFSocialConnectionStateTests(TestCase):
    def test_email_identity_does_not_imply_google_or_github_connection(self):
        user = User.objects.create_user(username="social-state", email="person@gmail.test", password="pass")
        EmailAddress.objects.create(user=user, email="github@example.test", verified=True)
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard:account"))
        self.assertContains(response, "Google")
        self.assertContains(response, "GitHub")
        self.assertEqual(response.content.decode().count("Non connecté"), 2)

        SocialAccount.objects.create(user=user, provider="google", uid="google-uid")
        response = self.client.get(reverse("dashboard:account"))
        self.assertEqual(response.content.decode().count("Connecté"), 1)
        self.assertEqual(response.content.decode().count("Non connecté"), 1)
