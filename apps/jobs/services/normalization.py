import traceback
from dateutil import parser as date_parser

from django.contrib.postgres.search import SearchVector
from apps.jobs.models import (
    RawJobRecord,
    NormalizedJob,
    NormalizationStatus,
)
from apps.jobs.services.classification import JobClassificationService


class JobNormalizationService:
    @staticmethod
    def normalize(raw_record: RawJobRecord) -> NormalizedJob | None:
        payload = raw_record.raw_payload_json

        if not isinstance(payload, dict):
            raw_record.normalization_status = NormalizationStatus.FAILED
            raw_record.normalization_error = "Invalid payload: expected object"
            raw_record.save(update_fields=["normalization_status", "normalization_error"])
            return None

        title = payload.get("intitule")
        if not title:
            raw_record.normalization_status = NormalizationStatus.FAILED
            raw_record.normalization_error = "Missing title ('intitule')"
            raw_record.save(update_fields=["normalization_status", "normalization_error"])
            return None

        description = payload.get("description", "")
        
        try:
            classification = JobClassificationService.classify(payload, description, title)

            entreprise = payload.get("entreprise") or {}
            company_name = entreprise.get("nom", "")

            lieu = payload.get("lieuTravail") or {}
            location_str = lieu.get("libelle", "")
            city = lieu.get("commune", "")
            department = lieu.get("codePostal", "")[:2] if lieu.get("codePostal") else ""
            region = ""  # Could be derived from codePostal later

            published_at = None
            date_creation = payload.get("dateCreation")
            if date_creation:
                try:
                    published_at = date_parser.parse(date_creation)
                except (ValueError, TypeError):
                    pass

            origine_offre = payload.get("origineOffre") or {}
            source_url = origine_offre.get("urlOrigine", "")

            raw_skills = payload.get("competences") or []
            if not isinstance(raw_skills, list):
                raw_skills = []
            required_skills = []
            optional_skills = []
            for skill_entry in raw_skills:
                if not isinstance(skill_entry, dict):
                    continue
                skill_label = skill_entry.get("libelle")
                if not isinstance(skill_label, str) or not skill_label.strip():
                    continue
                if skill_entry.get("exigence") == "E":
                    required_skills.append(skill_label)
                else:
                    optional_skills.append(skill_label)

            job, _created = NormalizedJob.objects.update_or_create(
                source=raw_record.source,
                source_job_id=raw_record.source_job_id,
                defaults={
                    "raw_record": raw_record,
                    "title": title,
                    "company_name": company_name,
                    "location": location_str,
                    "city": city,
                    "department": department,
                    "region": region,
                    "contract_type": payload.get("typeContrat", ""),
                    "remote_type": classification["remote_type"],
                    "job_type": classification["job_type"],
                    "experience_level": classification["experience_level"],
                    "description": description,
                    "source_url": source_url,
                    "published_at": published_at,
                    "first_seen_at": raw_record.first_seen_at,
                    "last_seen_at": raw_record.last_seen_at,
                    "last_fetched_at": raw_record.last_fetched_at,
                    "language_requirements_json": classification["language_requirements"],
                    "required_skills_json": required_skills,
                    "optional_skills_json": optional_skills,
                }
            )

            NormalizedJob.objects.filter(id=job.id).update(
                search_vector=(
                    SearchVector("title", weight="A")
                    + SearchVector("company_name", weight="B")
                    + SearchVector("location", weight="C")
                    + SearchVector("description", weight="D")
                )
            )
            job.refresh_from_db()

            raw_record.normalization_status = NormalizationStatus.SUCCESS
            raw_record.normalization_error = ""
            raw_record.save(update_fields=["normalization_status", "normalization_error"])
            
            return job

        except Exception:
            raw_record.normalization_status = NormalizationStatus.FAILED
            raw_record.normalization_error = traceback.format_exc()
            raw_record.save(update_fields=["normalization_status", "normalization_error"])
            return None

    @staticmethod
    def normalize_record_by_id(raw_record_id: int) -> str:
        try:
            raw_record = RawJobRecord.objects.get(id=raw_record_id)
        except RawJobRecord.DoesNotExist:
            return f"RawJobRecord {raw_record_id} does not exist."

        job = JobNormalizationService.normalize(raw_record)
        if job is None:
            return f"Failed to normalize raw record {raw_record_id}"

        from apps.jobs.services.skill_extraction import JobSkillExtractionService

        JobSkillExtractionService.extract_for_job(job)
        return f"Normalized raw record {raw_record_id} into job {job.id}"
