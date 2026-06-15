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
        self.assertLessEqual(skills_count, 330)
        self.assertGreaterEqual(aliases_count, 500)
        
        # Check required aliases
        react_alias = SkillAlias.objects.get(normalized_alias="reactjs")
        self.assertEqual(react_alias.skill.canonical_name, "React")
        
        postgres_alias = SkillAlias.objects.get(normalized_alias="postgres")
        self.assertEqual(postgres_alias.skill.canonical_name, "PostgreSQL")

    def test_seed_command(self):
        out = StringIO()
        call_command('seed_skills', stdout=out)
        self.assertIn("Successfully seeded taxonomy", out.getvalue())
