"""Isolated tests for the deterministic ``skill_uid`` migration chain.

Every test runs inside the database created by Django's test runner.
``MigrationExecutor`` moves that test database between historical states,
and teardown always restores the current migration leaves. No persistent
database name or normal development database connection is used here.
"""

import importlib
import uuid

from django.core.exceptions import FieldDoesNotExist
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models import NOT_PROVIDED
from django.test import TransactionTestCase


MIGRATION_INITIAL = ("skills", "0001_initial")
MIGRATION_NULLABLE = ("skills", "0002_skill_skill_uid_nullable")
MIGRATION_POPULATE = ("skills", "0003_populate_skill_uid")
MIGRATION_FINALIZE = ("skills", "0004_skill_skill_uid_finalize")

INVALID_ARTIFACT_NAME = "Langues non précisées"
INVALID_ARTIFACT_TOMBSTONE = uuid.UUID(
    "0b71fefd-ea81-42e1-a4e1-2d84d3497960"
)


class SkillUidMigrationTests(TransactionTestCase):
    """Exercise historical states using only Django's test database."""

    databases = {"default"}

    def setUp(self):
        super().setUp()
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([MIGRATION_INITIAL])
        self.initial_apps = self.executor.loader.project_state(
            [MIGRATION_INITIAL]
        ).apps

    def tearDown(self):
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
        finally:
            super().tearDown()

    def _create_skill(
        self,
        canonical_name,
        *,
        slug=None,
        category="other",
        is_active=True,
        source="manual",
    ):
        Skill = self.initial_apps.get_model("skills", "Skill")
        return Skill.objects.create(
            canonical_name=canonical_name,
            slug=slug or canonical_name.lower().replace(" ", "-").replace(".", "dot"),
            category=category,
            is_active=is_active,
            source=source,
        )

    def _migrate_to(self, target):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([target])
        return self.executor.loader.project_state([target]).apps

    def _skill_uid_column(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT is_nullable, data_type "
                "FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'skills_skill' "
                "AND column_name = 'skill_uid'"
            )
            return cursor.fetchone()

    def _skill_uid_unique_constraints(self):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, "skills_skill"
            )
        return [
            details
            for details in constraints.values()
            if details.get("unique") and details.get("columns") == ["skill_uid"]
        ]

    def test_step1_field_is_nullable_uuid_without_default_or_unique(self):
        apps = self._migrate_to(MIGRATION_NULLABLE)
        Skill = apps.get_model("skills", "Skill")
        field = Skill._meta.get_field("skill_uid")

        self.assertEqual(field.get_internal_type(), "UUIDField")
        self.assertTrue(field.null)
        self.assertFalse(field.unique)
        self.assertIs(field.default, NOT_PROVIDED)
        self.assertEqual(self._skill_uid_column(), ("YES", "uuid"))
        self.assertEqual(self._skill_uid_unique_constraints(), [])

    def test_step2_assigns_every_embedded_registry_uuid_exactly(self):
        migration = importlib.import_module(
            "apps.skills.migrations.0003_populate_skill_uid"
        )
        expected = migration.REGISTRY_UUID_BY_CANONICAL
        Skill = self.initial_apps.get_model("skills", "Skill")
        Skill.objects.bulk_create(
            [
                Skill(
                    canonical_name=name,
                    slug=f"registry-skill-{index}",
                    category="other",
                    is_active=True,
                    source="seed",
                )
                for index, name in enumerate(expected)
            ]
        )

        apps = self._migrate_to(MIGRATION_POPULATE)
        MigratedSkill = apps.get_model("skills", "Skill")
        actual = {
            name: str(skill_uid)
            for name, skill_uid in MigratedSkill.objects.values_list(
                "canonical_name", "skill_uid"
            )
        }

        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 522)

    def test_step2_dotnet_old_only_receives_target_identity(self):
        self._create_skill(
            ".NET Core", slug="dotnet-core", category="backend"
        )
        apps = self._migrate_to(MIGRATION_POPULATE)
        Skill = apps.get_model("skills", "Skill")
        row = Skill.objects.get(canonical_name=".NET Core")

        self.assertEqual(
            str(row.skill_uid),
            "4a251d4e-4420-4b49-a0d7-eba352f9cf5f",
        )

    def test_step2_dotnet_old_and_target_receive_distinct_identities(self):
        self._create_skill(
            ".NET Core", slug="dotnet-core", category="backend"
        )
        self._create_skill(".NET", slug="dotnet", category="backend")
        apps = self._migrate_to(MIGRATION_POPULATE)
        Skill = apps.get_model("skills", "Skill")
        rows = {
            row.canonical_name: row
            for row in Skill.objects.filter(
                canonical_name__in=[".NET Core", ".NET"]
            )
        }

        self.assertEqual(
            str(rows[".NET"].skill_uid),
            "4a251d4e-4420-4b49-a0d7-eba352f9cf5f",
        )
        self.assertEqual(
            str(rows[".NET Core"].skill_uid),
            "23b14296-d0ce-4897-a7fc-1489331f86de",
        )
        self.assertNotEqual(
            rows[".NET"].skill_uid,
            rows[".NET Core"].skill_uid,
        )

    def test_step2_aspnet_old_only_receives_target_identity(self):
        self._create_skill(
            "ASP.NET", slug="aspdotnet", category="backend"
        )
        apps = self._migrate_to(MIGRATION_POPULATE)
        Skill = apps.get_model("skills", "Skill")
        row = Skill.objects.get(canonical_name="ASP.NET")

        self.assertEqual(
            str(row.skill_uid),
            "913a7b10-86d5-4f2e-b57a-c77c192e27b4",
        )

    def test_step2_invalid_artifact_is_tombstoned_inactive_with_relation(self):
        artifact = self._create_skill(
            INVALID_ARTIFACT_NAME,
            slug="langues-non-precisees",
            is_active=True,
            source="legacy_artifact",
        )
        SkillAlias = self.initial_apps.get_model("skills", "SkillAlias")
        alias = SkillAlias.objects.create(
            skill=artifact,
            alias="langues inconnues",
            normalized_alias="langues inconnues",
            language="fr",
        )

        apps = self._migrate_to(MIGRATION_POPULATE)
        Skill = apps.get_model("skills", "Skill")
        MigratedAlias = apps.get_model("skills", "SkillAlias")
        migrated = Skill.objects.get(pk=artifact.pk)
        migrated_alias = MigratedAlias.objects.get(pk=alias.pk)

        self.assertEqual(migrated.skill_uid, INVALID_ARTIFACT_TOMBSTONE)
        self.assertFalse(migrated.is_active)
        self.assertEqual(migrated_alias.skill_id, migrated.pk)

    def _assert_unknown_row_aborts(self, *, is_active):
        state = "Active" if is_active else "Inactive"
        name = f"Unknown {state} Skill"
        self._create_skill(
            "Python", slug="python", category="programming_language"
        )
        self._create_skill(
            name,
            slug=f"unknown-{state.lower()}",
            is_active=is_active,
        )

        with self.assertRaisesRegex(RuntimeError, name) as raised:
            self._migrate_to(MIGRATION_POPULATE)
        self.assertIn(state.lower(), str(raised.exception))

        # The failed data migration is atomic. Remove only the deliberate
        # unknown fixture so teardown can restore the current leaf safely.
        Skill = self.initial_apps.get_model("skills", "Skill")
        Skill.objects.filter(canonical_name=name).delete()

    def test_step2_unknown_active_row_aborts(self):
        self._assert_unknown_row_aborts(is_active=True)

    def test_step2_unknown_inactive_row_aborts(self):
        self._assert_unknown_row_aborts(is_active=False)

    def test_step3_finalized_values_are_non_null_unique_uuidv4(self):
        for name, slug in (
            ("Python", "python"),
            ("PostgreSQL", "postgresql"),
            (".NET Core", "dotnet-core"),
            (".NET", "dotnet"),
            (INVALID_ARTIFACT_NAME, "langues-non-precisees"),
        ):
            self._create_skill(name, slug=slug)

        apps = self._migrate_to(MIGRATION_FINALIZE)
        Skill = apps.get_model("skills", "Skill")
        values = list(Skill.objects.values_list("skill_uid", flat=True))

        self.assertEqual(len(values), 5)
        self.assertTrue(all(value is not None for value in values))
        self.assertEqual(len(values), len(set(values)))
        self.assertTrue(all(value.version == 4 for value in values))
        artifact = Skill.objects.get(canonical_name=INVALID_ARTIFACT_NAME)
        self.assertFalse(artifact.is_active)

    def test_step3_field_is_non_null_unique_with_creation_default(self):
        apps = self._migrate_to(MIGRATION_FINALIZE)
        Skill = apps.get_model("skills", "Skill")
        field = Skill._meta.get_field("skill_uid")

        self.assertFalse(field.null)
        self.assertTrue(field.unique)
        self.assertIsNot(field.default, NOT_PROVIDED)
        self.assertEqual(self._skill_uid_column(), ("NO", "uuid"))
        self.assertEqual(len(self._skill_uid_unique_constraints()), 1)

    def test_reverse_from_finalize_to_initial_removes_field(self):
        self._migrate_to(MIGRATION_FINALIZE)
        apps = self._migrate_to(MIGRATION_INITIAL)
        Skill = apps.get_model("skills", "Skill")

        with self.assertRaises(FieldDoesNotExist):
            Skill._meta.get_field("skill_uid")
        self.assertIsNone(self._skill_uid_column())
