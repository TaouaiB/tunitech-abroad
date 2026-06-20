from django.test import TestCase
from apps.skills.models import Skill, SkillAlias
from apps.skills.services.seed import SkillSeedService
from django.core.management import call_command
from io import StringIO

class SeedServiceTests(TestCase):
    def test_seed_is_idempotent(self):
        # Run 1
        result1 = SkillSeedService.seed_initial_taxonomy()
        self.assertGreater(result1["skills_created"], 100)
        self.assertGreater(result1["aliases_created"], 100)

        # Run 2
        result2 = SkillSeedService.seed_initial_taxonomy()
        self.assertEqual(result2["skills_created"], 0)
        self.assertEqual(result2["aliases_created"], 0)

        # Check counts
        skills_count = Skill.objects.count()
        aliases_count = SkillAlias.objects.count()
        self.assertGreaterEqual(skills_count, 200)
        self.assertLessEqual(skills_count, 550)
        self.assertGreaterEqual(aliases_count, 500)
        self.assertEqual(SkillAlias.objects.values("normalized_alias").distinct().count(), aliases_count)

        # Check required aliases
        react_alias = SkillAlias.objects.get(normalized_alias="reactjs")
        self.assertEqual(react_alias.skill.canonical_name, "React")

        postgres_alias = SkillAlias.objects.get(normalized_alias="postgres")
        self.assertEqual(postgres_alias.skill.canonical_name, "PostgreSQL")

    def test_seed_command(self):
        out = StringIO()
        call_command('seed_skills', stdout=out)
        self.assertIn("Successfully seeded taxonomy", out.getvalue())

    def test_high_value_aliases(self):
        from apps.skills.services.normalizer import normalize_skill_text
        SkillSeedService.seed_initial_taxonomy()

        mappings = [
            ("Cybersécurité", "Cybersecurity"),
            ("Cybersecurité", "Cybersecurity"),
            ("API REST", "REST API"),
            ("Windows", "Windows"),
            ("Active Directory", "Active Directory"),
            ("Réseaux", "Network Security"),
            ("DevOps", "DevOps"),
            ("Cloud", "Cloud"),
            ("PowerShell", "PowerShell"),
            ("ISO 27001", "ISO 27001"),
            ("SIEM", "SIEM"),
            ("Microsoft 365", "Microsoft 365"),
            ("Data Modeling", "Data Modeling"),
            ("Développement logiciel", "Software Development"),
            ("Assistance technique", "IT Support"),
        ]

        for alias_raw, canonical in mappings:
            alias_norm = normalize_skill_text(alias_raw)
            alias_obj = SkillAlias.objects.get(normalized_alias=alias_norm)
            self.assertEqual(alias_obj.skill.canonical_name, canonical)

    def test_phase_15b_aliases_are_idempotent_without_duplicates(self):
        SkillSeedService.seed_initial_taxonomy()

        first_skill_count = Skill.objects.count()
        first_alias_count = SkillAlias.objects.count()

        result = SkillSeedService.seed_initial_taxonomy()

        self.assertEqual(result["skills_created"], 0)
        self.assertEqual(result["aliases_created"], 0)
        self.assertEqual(result["alias_conflicts"], [])
        self.assertEqual(Skill.objects.count(), first_skill_count)
        self.assertEqual(SkillAlias.objects.count(), first_alias_count)
        self.assertEqual(SkillAlias.objects.values("normalized_alias").distinct().count(), first_alias_count)

    def test_alias_conflicts_are_reported_and_not_remapped(self):
        from apps.skills.services.normalizer import normalize_skill_text
        wrong_skill = Skill.objects.create(canonical_name="Wrong Skill", slug="wrong-skill")
        SkillAlias.objects.create(skill=wrong_skill, alias="Cybersécurité", normalized_alias=normalize_skill_text("Cybersécurité"))

        result = SkillSeedService.seed_initial_taxonomy()

        alias_obj = SkillAlias.objects.get(normalized_alias=normalize_skill_text("Cybersécurité"))
        self.assertEqual(alias_obj.skill.canonical_name, "Wrong Skill")
        self.assertIn(
            {
                "alias": "Cybersécurité",
                "normalized_alias": "cybersecurite",
                "existing_skill": "Wrong Skill",
                "requested_skill": "Cybersecurity",
            },
            result["alias_conflicts"],
        )

    def test_phase_15d_curated_seed_is_idempotent_without_duplicate_aliases(self):
        SkillSeedService.seed_initial_taxonomy()

        first_skill_count = Skill.objects.count()
        first_alias_count = SkillAlias.objects.count()

        result = SkillSeedService.seed_initial_taxonomy()

        self.assertEqual(result["skills_created"], 0)
        self.assertEqual(result["aliases_created"], 0)
        self.assertEqual(Skill.objects.count(), first_skill_count)
        self.assertEqual(SkillAlias.objects.count(), first_alias_count)
        self.assertEqual(Skill.objects.values("canonical_name").distinct().count(), first_skill_count)
        self.assertEqual(SkillAlias.objects.values("normalized_alias").distinct().count(), first_alias_count)

        self.assertTrue(Skill.objects.filter(canonical_name="Frontend Development").exists())
        self.assertEqual(
            SkillAlias.objects.get(normalized_alias="front end development").skill.canonical_name,
            "Frontend Development",
        )
        self.assertEqual(
            SkillAlias.objects.get(normalized_alias="agile methodologies").skill.canonical_name,
            "Agile",
        )

    def test_phase_15d_already_resolved_rows_do_not_create_duplicate_aliases(self):
        SkillSeedService.seed_initial_taxonomy()

        self.assertEqual(SkillAlias.objects.filter(normalized_alias="windows").count(), 1)
        self.assertEqual(SkillAlias.objects.get(normalized_alias="windows").skill.canonical_name, "Windows")
