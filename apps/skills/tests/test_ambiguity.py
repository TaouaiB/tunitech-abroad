from django.test import TestCase

from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.normalizer import SkillNormalizerService, normalize_skill_text


class SkillAmbiguityRulesTests(TestCase):
    def setUp(self):
        self.skills = {}
        for canonical, aliases in {
            "Chef": ["Chef"],
            "SQL": ["SQL"],
            "SQL Server": ["SQL Server"],
            "PostgreSQL": ["PostgreSQL", "Postgres"],
            "MySQL": ["MySQL"],
            "SQLite": ["SQLite"],
            "Go": ["Go", "Golang"],
            "C": ["C"],
            "C++": ["C++"],
            "R": ["R"],
            "Spring Boot": ["Spring Boot", "Spring", "Spring Framework"],
            "Oracle DB": ["Oracle DB", "Oracle", "Oracle Database", "Oracle PL/SQL"],
        }.items():
            skill = Skill.objects.create(
                canonical_name=canonical,
                slug=canonical.lower().replace("+", "plus").replace("#", "sharp").replace(" ", "-"),
            )
            self.skills[canonical] = skill
            for alias in aliases:
                SkillAlias.objects.create(skill=skill, alias=alias, normalized_alias=normalize_skill_text(alias))

    def _canonical_names(self, raw_skills):
        result = SkillNormalizerService.normalize_many(raw_skills, source_type="cv")
        return {skill.canonical_name for skill in result.canonical_skills}

    def test_chef_role_and_food_contexts_do_not_map_to_devops_chef(self):
        rejected = [
            "chef de projet",
            "chef d'équipe",
            "chef d'equipe",
            "chef de produit",
            "chef cuisinier",
            "restaurant chef",
            "kitchen chef",
            "head chef",
        ]
        for phrase in rejected:
            with self.subTest(phrase=phrase):
                self.assertNotIn("Chef", self._canonical_names([phrase]))

    def test_chef_devops_context_maps_to_chef(self):
        accepted = ["Chef cookbooks", "Chef Infra", "Chef recipes", "configuration management with Chef", "DevOps Chef"]
        for phrase in accepted:
            with self.subTest(phrase=phrase):
                self.assertIn("Chef", self._canonical_names([phrase]))

    def test_sql_family_skills_do_not_create_generic_sql_without_standalone_sql(self):
        cases = [
            ("SQL Server", "SQL Server"),
            ("PostgreSQL", "PostgreSQL"),
            ("MySQL", "MySQL"),
            ("SQLite", "SQLite"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                names = self._canonical_names([raw])
                self.assertIn(expected, names)
                self.assertNotIn("SQL", names)

    def test_standalone_sql_and_nosql_rules(self):
        accepted = ["SQL queries", "SQL optimization", "advanced SQL", "maîtrise de SQL", "proficiency in SQL"]
        for phrase in accepted:
            with self.subTest(phrase=phrase):
                self.assertIn("SQL", self._canonical_names([phrase]))

        self.assertNotIn("SQL", self._canonical_names(["NoSQL"]))

    def test_short_aliases_require_safe_context(self):
        rejected_cases = {
            "Go": ["go to", "go live", "go-to-market", "go/no-go"],
            "C": ["C-level", "category C", "permis C", "section C"],
            "R": ["R&D", "R and D"],
            "Spring Boot": ["spring season", "spring internship"],
        }
        for canonical, phrases in rejected_cases.items():
            for phrase in phrases:
                with self.subTest(canonical=canonical, phrase=phrase):
                    self.assertNotIn(canonical, self._canonical_names([phrase]))

        accepted_cases = {
            "Go": ["Golang", "Go developer", "Go programming", "backend Go"],
            "C": ["C programming", "ANSI C", "embedded C"],
            "R": ["R programming", "R Shiny"],
            "Spring Boot": ["Spring Boot", "Spring Framework"],
            "Oracle DB": ["Oracle Database", "Oracle PL/SQL"],
        }
        for canonical, phrases in accepted_cases.items():
            for phrase in phrases:
                with self.subTest(canonical=canonical, phrase=phrase):
                    self.assertIn(canonical, self._canonical_names([phrase]))

    def test_c_cpp_maps_both_c_and_cpp(self):
        names = self._canonical_names(["C/C++"])
        self.assertIn("C", names)
        self.assertIn("C++", names)

    def test_metadata_noise_is_ignored_not_matched(self):
        result = SkillNormalizerService.normalize_many(
            ["source", "status", "statut", "vérifié", "verified", "à vérifier", "badge", "certifié"],
            source_type="cv",
        )

        self.assertEqual(result.canonical_skills, [])
        self.assertFalse(UnmatchedSkillCandidate.objects.exists())
