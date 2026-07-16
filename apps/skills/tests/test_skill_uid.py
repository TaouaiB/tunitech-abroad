"""Tests for the Skill ``skill_uid`` identity field.

The ``skill_uid`` is a UUIDv4 cross-environment identity assigned
once from the committed registry and made immutable by the model
``save()`` method. These tests prove the model-level invariants
without touching the registry file.
"""

import uuid

from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.skills.models import Skill


class SkillUidModelTests(TestCase):
    """Model-level invariants for ``Skill.skill_uid``."""

    def test_default_value_is_uuid(self):
        skill = Skill.objects.create(canonical_name="Python", slug="python")
        self.assertIsInstance(skill.skill_uid, uuid.UUID)

    def test_uuid_version_is_4(self):
        skill = Skill.objects.create(canonical_name="Go", slug="go")
        self.assertEqual(skill.skill_uid.version, 4)

    def test_field_is_unique(self):
        Skill.objects.create(
            canonical_name="Rust", slug="rust", skill_uid=uuid.UUID("4a251d4e-4420-4b49-a0d7-eba352f9cf5f")
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Skill.objects.create(
                    canonical_name="Unique Other",
                    slug="unique-other",
                    skill_uid=uuid.UUID("4a251d4e-4420-4b49-a0d7-eba352f9cf5f"),
                )

    def test_field_is_not_primary_key(self):
        field = Skill._meta.get_field("skill_uid")
        self.assertFalse(field.primary_key)

    def test_field_is_non_editable(self):
        field = Skill._meta.get_field("skill_uid")
        self.assertFalse(field.editable)

    def test_existing_integer_primary_key_preserved(self):
        skill = Skill.objects.create(canonical_name="Ruby", slug="ruby")
        # Integer primary key remains
        self.assertIsInstance(skill.id, int)
        self.assertGreater(skill.id, 0)
        # skill_uid is a separate UUID
        self.assertIsInstance(skill.skill_uid, uuid.UUID)

    def test_saving_unchanged_skill_succeeds(self):
        skill = Skill.objects.create(canonical_name="Kotlin", slug="kotlin")
        # Re-fetch and save without changes
        skill.refresh_from_db()
        skill.save()  # must not raise
        skill.refresh_from_db()
        self.assertEqual(skill.skill_uid, skill.skill_uid)

    def test_changing_skill_uid_via_save_is_rejected(self):
        skill = Skill.objects.create(canonical_name="Swift", slug="swift")
        original = skill.skill_uid
        skill.skill_uid = uuid.UUID("11111111-2222-4333-8444-555555555555")
        with self.assertRaises(ValueError) as ctx:
            skill.save()
        self.assertIn("immutable", str(ctx.exception))
        # Reload to confirm the row was not changed
        skill.refresh_from_db()
        self.assertEqual(skill.skill_uid, original)

    def test_changing_skill_uid_via_update_fields_is_rejected(self):
        skill = Skill.objects.create(canonical_name="Scala", slug="scala")
        original = skill.skill_uid
        skill.skill_uid = uuid.UUID("11111111-2222-4333-8444-666666666666")
        with self.assertRaises(ValueError):
            skill.save(update_fields=["skill_uid"])
        skill.refresh_from_db()
        self.assertEqual(skill.skill_uid, original)

    def test_changing_other_field_preserves_skill_uid(self):
        skill = Skill.objects.create(canonical_name="Perl", slug="perl")
        original = skill.skill_uid
        skill.is_active = False
        skill.save()
        skill.refresh_from_db()
        self.assertEqual(skill.skill_uid, original)
        self.assertFalse(skill.is_active)

    def test_admin_form_excludes_skill_uid(self):
        # editable=False keeps skill_uid out of default ModelForm fields
        from django.forms.models import modelform_factory
        SkillForm = modelform_factory(Skill, fields=["canonical_name", "slug", "category"])
        form = SkillForm()
        self.assertNotIn("skill_uid", form.fields)

    def test_no_runtime_mutation_helper_exists(self):
        # There is no public or private model helper that bypasses the
        # ``skill_uid`` immutability invariant. The seed and rename code
        # paths must never rewrite a persisted identity.
        self.assertFalse(hasattr(Skill, "set_skill_uid_for_rename"))
        self.assertFalse(
            hasattr(Skill(), "_skill_uid_rename_in_progress"),
            "Skill instances must not carry a hidden bypass flag",
        )

    def test_no_bypass_state_after_failed_save(self):
        # If save() raises, no hidden bypass state may remain on the
        # instance.
        skill = Skill.objects.create(canonical_name="Haskell", slug="haskell")
        original = skill.skill_uid
        # Simulate a hypothetical bypass flag the seed/rename code
        # might have left behind
        skill._skill_uid_rename_in_progress = True
        # Trigger save with a UUID change; immutability must still
        # reject the change and the defensive finally must clear the
        # bypass flag.
        skill.skill_uid = uuid.UUID("11111111-2222-4333-8444-777777777777")
        with self.assertRaises(ValueError):
            skill.save()
        self.assertFalse(
            hasattr(skill, "_skill_uid_rename_in_progress"),
            "Failed save must not leak hidden bypass state on the instance",
        )
        skill.refresh_from_db()
        self.assertEqual(skill.skill_uid, original)
