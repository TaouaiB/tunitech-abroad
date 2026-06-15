from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate

class SkillModelTests(TestCase):
    def test_duplicate_slug_rejected(self):
        Skill.objects.create(canonical_name="Python", slug="python")
        with self.assertRaises(IntegrityError):
            Skill.objects.create(canonical_name="Python 2", slug="python")

    def test_duplicate_canonical_name_rejected(self):
        Skill.objects.create(canonical_name="Python", slug="python")
        with self.assertRaises(IntegrityError):
            Skill.objects.create(canonical_name="Python", slug="python-2")

class SkillAliasModelTests(TestCase):
    def setUp(self):
        self.skill = Skill.objects.create(canonical_name="React", slug="react")

    def test_duplicate_normalized_alias_rejected(self):
        SkillAlias.objects.create(skill=self.skill, alias="ReactJS", normalized_alias="reactjs")
        with self.assertRaises(IntegrityError):
            SkillAlias.objects.create(skill=self.skill, alias="React.js", normalized_alias="reactjs")

class UnmatchedSkillCandidateTests(TestCase):
    def test_unique_normalized_text_source_type(self):
        UnmatchedSkillCandidate.objects.create(raw_skill_text="Unknown Skill", normalized_text="unknown skill", source_type="cv")
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                UnmatchedSkillCandidate.objects.create(raw_skill_text="Unknown", normalized_text="unknown skill", source_type="cv")
        
        # Different source type is allowed
        UnmatchedSkillCandidate.objects.create(raw_skill_text="Unknown", normalized_text="unknown skill", source_type="job")
