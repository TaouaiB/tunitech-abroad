from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import (
    JobSource,
    NormalizedJob,
    NormalizedJobSkill,
    RawJobRecord,
    RequirementType,
    SkillExtractionStatus,
    SourceType,
)
from apps.jobs.services.skill_extraction import JobSkillExtractionService
from apps.jobs.services.skill_materialization import JobSkillMaterializationService
from apps.skills.services.seed import SkillSeedService


class GateBSkillExtractionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SkillSeedService.seed_initial_taxonomy()
        cls.source = JobSource.objects.create(
            name="Gate B",
            slug="gate-b",
            source_type=SourceType.MANUAL,
        )

    def _job(self, *, title: str, description: str, source_job_id: str, raw_payload=None) -> NormalizedJob:
        raw_record = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=source_job_id,
            raw_payload_json=raw_payload or {},
            payload_hash=f"hash-{source_job_id}",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
        )
        return NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw_record,
            source_job_id=source_job_id,
            title=title,
            description=description,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
            classification_json={"is_it": True, "confidence": "high", "family": "software_development"},
        )

    def _materialized(self, job: NormalizedJob) -> dict[str, str]:
        return {
            row.skill.canonical_name: row.requirement_type
            for row in NormalizedJobSkill.objects.filter(job=job).select_related("skill")
        }

    def test_chef_de_projet_does_not_materialize_devops_chef(self):
        job = self._job(
            title="Chef de projet informatique",
            description="Coordination projet, communication et suivi planning.",
            source_job_id="chef-project",
        )

        JobSkillExtractionService.extract_for_job(job)

        self.assertNotIn("Chef", self._materialized(job))

    def test_chef_devops_context_still_materializes_chef(self):
        job = self._job(
            title="Ingénieur DevOps",
            description="Stack technique: Chef cookbooks, Linux et automatisation infrastructure.",
            source_job_id="chef-devops",
        )

        JobSkillExtractionService.extract_for_job(job)

        self.assertEqual(self._materialized(job).get("Chef"), RequirementType.REQUIRED.value)

    def test_sql_server_does_not_duplicate_plain_sql(self):
        job = self._job(
            title="Développeur base de données",
            description="Stack technique obligatoire: SQL Server, C# et .NET.",
            source_job_id="sql-server",
        )

        JobSkillExtractionService.extract_for_job(job)

        materialized = self._materialized(job)
        self.assertEqual(materialized.get("SQL Server"), RequirementType.REQUIRED.value)
        self.assertNotIn("SQL", materialized)

    def test_postgresql_mysql_sqlite_stay_distinct_from_plain_sql(self):
        job = self._job(
            title="Database developer",
            description="Stack technique obligatoire: PostgreSQL, MySQL et SQLite.",
            source_job_id="sql-family",
        )

        JobSkillExtractionService.extract_for_job(job)

        materialized = self._materialized(job)
        self.assertIn("PostgreSQL", materialized)
        self.assertIn("MySQL", materialized)
        self.assertIn("SQLite", materialized)
        self.assertNotIn("SQL", materialized)

    def test_specific_api_skills_survive_but_plain_api_is_not_required(self):
        specific = self._job(
            title="Backend developer",
            description="Stack technique obligatoire: REST API, OpenAPI et GraphQL.",
            source_job_id="specific-api",
        )
        JobSkillExtractionService.extract_for_job(specific)
        specific_materialized = self._materialized(specific)
        self.assertEqual(specific_materialized.get("REST API"), RequirementType.REQUIRED.value)
        self.assertEqual(specific_materialized.get("Swagger"), RequirementType.REQUIRED.value)
        self.assertEqual(specific_materialized.get("GraphQL"), RequirementType.REQUIRED.value)
        self.assertNotIn("API", specific_materialized)

        plain = self._job(
            title="Développeur API",
            description="Compétences techniques obligatoires: API.",
            source_job_id="plain-api",
        )
        JobSkillExtractionService.extract_for_job(plain)
        plain_materialized = self._materialized(plain)
        self.assertNotEqual(plain_materialized.get("API"), RequirementType.REQUIRED.value)

    def test_soft_and_methodology_terms_do_not_become_missing_technical_skills(self):
        job = self._job(
            title="Consultant projet",
            description="",
            source_job_id="soft-method",
        )
        job.required_skills_json = ["Agile", "Scrum", "Communication", "Teamwork", "Leadership"]
        job.save(update_fields=["required_skills_json"])

        JobSkillMaterializationService.materialize_for_job(job, source="rule")
        job.refresh_from_db()

        self.assertFalse(NormalizedJobSkill.objects.filter(job=job).exists())
        self.assertNotIn(job.skill_signal_quality, {"strong", "partial"})

    def test_broad_process_terms_are_not_required_technical_skills(self):
        job = self._job(
            title="Analyste technique",
            description="",
            source_job_id="broad-process",
        )
        job.required_skills_json = [
            "Technical Documentation",
            "Technical Watch",
            "Corrective Maintenance",
            "Software Testing",
            "Software Development",
        ]
        job.save(update_fields=["required_skills_json"])

        JobSkillMaterializationService.materialize_for_job(job, source="rule")

        required_names = {
            row.skill.canonical_name
            for row in NormalizedJobSkill.objects.filter(
                job=job,
                requirement_type=RequirementType.REQUIRED.value,
            ).select_related("skill")
        }
        self.assertFalse(
            required_names.intersection(
                {
                    "Technical Documentation",
                    "Technical Watch",
                    "Corrective Maintenance",
                    "Software Testing",
                    "Software Development",
                }
            )
        )

    def test_zero_skill_and_generic_only_jobs_are_not_matchable_signal_quality(self):
        zero = self._job(
            title="Technicien informatique",
            description=(
                "Accompagnement utilisateurs et tâches générales sans stack technique précise. "
                "Le poste mentionne des activités informatiques de premier niveau, mais aucune "
                "technologie, aucun outil, aucun langage et aucune base de données exploitable."
            ),
            source_job_id="zero-skill",
        )

        JobSkillMaterializationService.materialize_for_job(zero, source="rule")
        zero.refresh_from_db()

        self.assertEqual(zero.skill_extraction_status, SkillExtractionStatus.SUCCESS)
        self.assertIn(zero.skill_signal_quality, {"missing", "generic_only"})

        generic = self._job(
            title="Développeur web",
            description="",
            source_job_id="generic-only",
            raw_payload={
                "competences": [
                    {"libelle": "Concevoir une application web", "exigence": "E"},
                    {"libelle": "Collaborer avec une équipe projet", "exigence": "S"},
                ]
            },
        )

        JobSkillMaterializationService.materialize_for_job(generic, source="rule")
        generic.refresh_from_db()

        self.assertFalse(NormalizedJobSkill.objects.filter(job=generic).exists())
        self.assertEqual(generic.skill_signal_quality, "generic_only")

    def test_france_travail_action_phrases_do_not_create_unmatched_candidates(self):
        from apps.skills.models import UnmatchedSkillCandidate

        job = self._job(
            title="Technicien informatique",
            description="Support utilisateur général.",
            source_job_id="ft-action-phrases",
            raw_payload={
                "competences": [
                    {"libelle": "Développer une application en lien avec une base de données", "exigence": "E"},
                    {"libelle": "Administrer un système d'informations", "exigence": "E"},
                    {"libelle": "Apporter une assistance technique aux équipes", "exigence": "S"},
                    {"libelle": "Diagnostiquer la nature et l'origine des incidents et mettre en oeuvre les mesures correctives", "exigence": "E"},
                ]
            },
        )

        before = UnmatchedSkillCandidate.objects.count()
        JobSkillExtractionService.extract_for_job(job)
        after = UnmatchedSkillCandidate.objects.count()

        self.assertEqual(before, after)
        self.assertFalse(NormalizedJobSkill.objects.filter(job=job).exists())

    def test_specific_api_job_is_not_generic_only_signal_quality(self):
        job = self._job(
            title="Backend developer",
            description="",
            source_job_id="specific-api-quality",
        )
        job.required_skills_json = ["REST API", "GraphQL"]
        job.save(update_fields=["required_skills_json"])

        JobSkillMaterializationService.materialize_for_job(job, source="rule")
        job.refresh_from_db()

        self.assertNotEqual(job.skill_signal_quality, "generic_only")
        self.assertIn(job.skill_signal_quality, {"strong", "partial"})
