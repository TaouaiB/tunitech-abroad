from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
import uuid
from contextlib import ExitStack, contextmanager
from dataclasses import asdict
from datetime import date, datetime, timezone as datetime_timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable
from unittest.mock import patch

import fitz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone

from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService
from apps.cvs.services.parsing import CVParsingService
from apps.cvs.services.text_extraction import CVTextExtractionService
from apps.jobs.models import (
    ExperienceLevel,
    JobSource,
    JobStatus,
    JobType,
    NormalizedJob,
    NormalizedJobSkill,
    RawJobRecord,
    RemoteType,
    RequirementType,
    SkillSource,
    SourceType,
)
from apps.jobs.services.skill_extraction import JobSkillExtractionService
from apps.matching.services.scoring import MatchScoringService
from apps.matching.models import MatchResult
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.recommendations.models import JobRecommendation, RecommendationRun
from apps.recommendations.services.recommendation import RecommendationService
from apps.skills.models import Skill, UnmatchedSkillCandidate
from apps.skills.services.normalizer import SkillNormalizerService, normalize_skill_text
from apps.skills.services.seed import SkillSeedService


BASELINE_FORMAT = "tuniatlas_ml_deterministic_baseline"
BASELINE_VERSION = "deterministic-v1"
EXPORTER_CONTRACT_VERSION = "1.0"
TAXONOMY_VERSION = "sha256:d6d5aebf5e4b958f163d2f33b8d441a36e6d638ac8c92379f18e6ebd40e2fc05"
TAXONOMY_SNAPSHOT_SHA256 = "f71e1a67420bebe00fe45ccb01ae508e5605178ce78bd9e5305780a0a93a002d"
TAXONOMY_MANIFEST_SHA256 = "0d410a706a19f05fa73b234bcd262ec8f85bf330c26fa3032295391e3ac09045"

EXPECTED_FILES = (
    "README.txt",
    "manifest.json",
    "cases.json",
    "job_extraction.json",
    "cv_extraction.json",
    "canonicalization.json",
    "matching_recommendation.json",
    "metrics.json",
    "known_failures.json",
    "SHA256SUMS",
)

DOMAIN_FILES = {
    "job_extraction": "job_extraction.json",
    "cv_extraction": "cv_extraction.json",
    "canonicalization": "canonicalization.json",
    "matching_recommendation": "matching_recommendation.json",
}

SERVICE_MODULES = (
    "apps/jobs/services/skill_extraction.py",
    "apps/jobs/services/skill_materialization.py",
    "apps/jobs/services/skill_signals.py",
    "apps/cvs/services/text_extraction.py",
    "apps/cvs/services/deterministic_extractor.py",
    "apps/cvs/services/parsing.py",
    "apps/skills/services/normalizer.py",
    "apps/skills/services/ambiguity.py",
    "apps/skills/services/extraction_policy.py",
    "apps/matching/services/scoring.py",
    "apps/matching/services/match_result.py",
    "apps/recommendations/services/recommendation.py",
    "apps/recommendations/services/query.py",
    "apps/core/baselines/deterministic.py",
)

CLASSIFICATIONS = {"CURRENT_OBSERVATION", "OBVIOUS_GOLD", "POLICY_PENDING"}
POLICY_STATUSES = {"known_failure", "policy_pending"}

ROOT = Path(__file__).resolve().parents[3]
FIXED_TIME = datetime(2020, 1, 15, 12, 0, tzinfo=datetime_timezone.utc)


class BaselineError(ValueError):
    """A controlled deterministic-baseline contract failure."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decimal_string(value: Decimal) -> str:
    if not value.is_finite():
        raise BaselineError("non-finite Decimal values are forbidden")
    normalized = value.normalize()
    rendered = format(normalized, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def canonical_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BaselineError("non-finite float values are forbidden")
        return value
    if isinstance(value, Decimal):
        return _decimal_string(value)
    if isinstance(value, uuid.UUID):
        return str(value).lower()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise BaselineError("naive datetimes are forbidden")
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise BaselineError("JSON object keys must be strings")
        return {key: canonical_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [canonical_value(item) for item in value]
        return sorted(converted, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    raise BaselineError(f"unsupported evidence type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            canonical_value(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _fixed_uuid(prefix: int, index: int) -> uuid.UUID:
    return uuid.UUID(f"{prefix:08x}-0000-4000-8000-{index:012d}")


def _skill_uid(skill: Skill) -> str:
    value = skill.skill_uid
    if value.version != 4:
        raise BaselineError(f"skill_uid is not UUIDv4: {skill.canonical_name}")
    return str(value).lower()


def _skill_record(skill: Skill) -> dict[str, str]:
    return {
        "canonical_name": skill.canonical_name,
        "category": skill.category,
        "skill_uid": _skill_uid(skill),
    }


def _skill_map() -> dict[str, Skill]:
    return {skill.canonical_name: skill for skill in Skill.objects.all()}


def _uids(names: Iterable[str], skills: dict[str, Skill]) -> list[str]:
    values = []
    for name in names:
        if name not in skills:
            raise BaselineError(f"synthetic fixture references unknown canonical skill: {name}")
        values.append(_skill_uid(skills[name]))
    return sorted(values)


def _case(
    *,
    case_id: str,
    domain: str,
    classification: str,
    synthetic_input: dict[str, Any],
    expected_present: Iterable[str] = (),
    expected_absent: Iterable[str] = (),
    skills: dict[str, Skill] | None = None,
) -> dict[str, Any]:
    if classification not in CLASSIFICATIONS:
        raise BaselineError(f"invalid fixture classification: {classification}")
    item: dict[str, Any] = {
        "case_id": case_id,
        "classification": classification,
        "domain": domain,
        "synthetic_input": synthetic_input,
    }
    if classification == "OBVIOUS_GOLD":
        if skills is None:
            raise BaselineError("obvious-gold skill expectations require a taxonomy")
        item["expected_absent_skill_uids"] = _uids(expected_absent, skills)
        item["expected_present_skill_uids"] = _uids(expected_present, skills)
    return item


JOB_FIXTURES: tuple[dict[str, Any], ...] = (
    {"id": "job_001", "title": "Python developer", "description": "Required: Python for backend services.", "present": ["Python"]},
    {"id": "job_002", "title": "Backend engineer", "description": "Hands-on experience with Python3 is required.", "present": ["Python"]},
    {"id": "job_003", "title": "API engineer", "description": "Required: Django Rest Framework (DRF).", "present": ["Django"]},
    {"id": "job_004", "title": "Frontend engineer", "description": "Stack technique: TYPESCRIPT and ReactJS.", "present": ["TypeScript", "React"]},
    {"id": "job_005", "title": "Platform developer", "description": "Required: C# services.", "present": ["C#"]},
    {"id": "job_006", "title": "Systems developer", "description": "Required: C++17 development.", "present": ["C++"]},
    {"id": "job_007", "title": ".NET developer", "description": "Required: .NET backend development.", "present": [".NET"]},
    {"id": "job_008", "title": "Backend developer", "description": "Required: .NET Core maintenance.", "present": [".NET"]},
    {"id": "job_009", "title": "Data engineer", "description": "Required: PostgreSQL administration.", "present": ["PostgreSQL"], "absent": ["SQL"]},
    {"id": "job_010", "title": "Database engineer", "description": "Required: SQL Server administration.", "present": ["SQL Server"], "absent": ["SQL"]},
    {"id": "job_011", "title": "Embedded developer", "description": "Required: SQLite storage.", "present": ["SQLite"], "absent": ["SQL"]},
    {"id": "job_012", "title": "Database developer", "description": "Required: MySQL query optimization.", "present": ["MySQL"], "absent": ["SQL"]},
    {"id": "job_013", "title": "Data analyst", "description": "Required: advanced SQL queries.", "present": ["SQL"]},
    {"id": "job_014", "title": "Java engineer", "description": "Required: Java microservices.", "present": ["Java"], "absent": ["JavaScript"]},
    {"id": "job_015", "title": "Web engineer", "description": "Required: JavaScript applications.", "present": ["JavaScript"], "absent": ["Java"]},
    {"id": "job_016", "title": "Frontend developer", "description": "Applications built with React and TypeScript.", "present": ["React", "TypeScript"]},
    {"id": "job_017", "title": "Incident coordinator", "description": "You must react to incidents quickly.", "absent": ["React"]},
    {"id": "job_018", "title": "DevOps engineer", "description": "Configuration management with Chef cookbooks and recipes.", "present": ["Chef"]},
    {"id": "job_019", "title": "Chef de projet", "description": "Le chef de projet coordonne une équipe produit.", "absent": ["Chef"]},
    {"id": "job_020", "title": "Chef d'équipe", "description": "Le chef d'équipe organise les horaires.", "absent": ["Chef"]},
    {"id": "job_021", "title": "Backend engineer", "description": "Services written in Go for internal tooling.", "present": ["Go"]},
    {"id": "job_022", "title": "Release coordinator", "description": "The release is ready to go to production.", "absent": ["Go"]},
    {"id": "job_023", "title": "Statistician", "description": "Statistical analysis in R for reporting.", "present": ["R"]},
    {"id": "job_024", "title": "Research coordinator", "description": "Join the R&D team for product studies.", "absent": ["R"]},
    {"id": "job_025", "title": "Java developer", "description": "Java Spring Boot microservices are required.", "present": ["Java", "Spring Boot"]},
    {"id": "job_026", "title": "Recruiting assistant", "description": "Support the spring recruitment campaign.", "absent": ["Spring Boot"]},
    {"id": "job_027", "title": "Python engineer", "description": "Email jobs@fixture.invalid or visit https://fixture.invalid; Python required.", "present": ["Python"]},
    {"id": "job_028", "title": "Python developer", "description": "Python Python PYTHON appears repeatedly.", "present": ["Python"]},
    {"id": "job_029", "title": "Mobile engineer", "description": "Work with APIs; Kotlin is listed at the very end: Kotlin", "present": ["Kotlin"]},
    {"id": "job_030", "title": "Synthetic role", "description": "Experience with QuasarFluxEngine is welcome."},
    {"id": "job_031", "title": "Synthetic role", "description": "Coordinate schedules and prepare reports."},
    {"id": "job_032", "title": "Ingénieur cloud", "description": "Compétences techniques indispensables : Kubernetes et Azure.", "present": ["Kubernetes", "Azure"]},
    {"id": "job_033", "title": "Reporting analyst", "description": "Create a tableau de suivi for weekly activity.", "absent": ["Tableau"]},
    {"id": "job_034", "title": "BI analyst", "description": "Build Tableau dashboards for finance.", "present": ["Tableau"]},
    {"id": "job_035", "title": "BI engineer", "description": "Power BI dashboards are mandatory.", "present": ["Power BI"]},
    {"id": "job_036", "title": "Reporting analyst", "description": "Prepare generic business intelligence reporting.", "absent": ["Power BI"]},
    {"id": "job_037", "title": "API developer", "description": "RESTful APIs with NodeJS are required.", "present": ["REST API", "Node.js"]},
    {"id": "job_038", "title": "DevOps engineer", "description": "Required: Docker and Kubernetes.", "present": ["Docker", "Kubernetes"]},
    {"id": "job_039", "title": "Embedded engineer", "description": "ANSI C programming for devices.", "present": ["C"]},
    {"id": "job_040", "title": "Executive assistant", "description": "Coordinate with C-level stakeholders.", "absent": ["C"]},
    {"id": "job_041", "title": "Go", "description": "Go", "classification": "POLICY_PENDING"},
    {"id": "job_042", "title": "R", "description": "R", "classification": "POLICY_PENDING"},
    {"id": "job_043", "title": "Spring", "description": "Spring", "classification": "POLICY_PENDING"},
)


CANONICAL_FIXTURES: tuple[dict[str, Any], ...] = (
    {"id": "canonical_001", "raw": ["Python"], "present": ["Python"]},
    {"id": "canonical_002", "raw": ["Python3"], "present": ["Python"]},
    {"id": "canonical_003", "raw": ["Django Rest Framework"], "present": ["Django"]},
    {"id": "canonical_004", "raw": ["JS"], "present": ["JavaScript"]},
    {"id": "canonical_005", "raw": ["TypeScript"], "present": ["TypeScript"]},
    {"id": "canonical_006", "raw": ["ReactJS"], "present": ["React"]},
    {"id": "canonical_007", "raw": ["NodeJS"], "present": ["Node.js"]},
    {"id": "canonical_008", "raw": ["Postgres"], "present": ["PostgreSQL"], "absent": ["SQL"]},
    {"id": "canonical_009", "raw": ["My SQL"], "present": ["MySQL"], "absent": ["SQL"]},
    {"id": "canonical_010", "raw": ["SQLite"], "present": ["SQLite"], "absent": ["SQL"]},
    {"id": "canonical_011", "raw": ["MSSQL"], "present": ["SQL Server"], "absent": ["SQL"]},
    {"id": "canonical_012", "raw": ["SQL"], "present": ["SQL"]},
    {"id": "canonical_013", "raw": ["Java"], "present": ["Java"], "absent": ["JavaScript"]},
    {"id": "canonical_014", "raw": ["JavaScript"], "present": ["JavaScript"], "absent": ["Java"]},
    {"id": "canonical_015", "raw": ["C++"], "present": ["C++"], "absent": ["C"]},
    {"id": "canonical_016", "raw": ["C Sharp"], "present": ["C#"]},
    {"id": "canonical_017", "raw": [".NET Core"], "present": [".NET"]},
    {"id": "canonical_018", "raw": ["dotnet"], "present": [".NET"]},
    {"id": "canonical_019", "raw": ["Spring Framework"], "present": ["Spring Boot"]},
    {"id": "canonical_020", "raw": ["AWS"], "present": ["AWS"]},
    {"id": "canonical_021", "raw": ["Docker"], "present": ["Docker"]},
    {"id": "canonical_022", "raw": ["Kubernetes"], "present": ["Kubernetes"]},
    {"id": "canonical_023", "raw": ["RESTful APIs"], "present": ["REST API"]},
    {"id": "canonical_024", "raw": ["Chef cookbooks"], "present": ["Chef"]},
    {"id": "canonical_025", "raw": ["Golang"], "present": ["Go"]},
    {"id": "canonical_026", "raw": ["RStudio"], "present": ["R"]},
    {"id": "canonical_027", "raw": ["QuasarFluxEngine"]},
    {"id": "canonical_028", "raw": ["Go"], "classification": "POLICY_PENDING"},
    {"id": "canonical_029", "raw": ["R"], "classification": "POLICY_PENDING"},
    {"id": "canonical_030", "raw": ["C"], "classification": "POLICY_PENDING"},
)


CV_FIXTURES: tuple[dict[str, Any], ...] = (
    {
        "id": "cv_001",
        "text": "Synthetic Candidate Alpha\ncandidate.alpha@fixture.invalid\nSKILLS\nPython, Django, PostgreSQL\n\nEXPERIENCE\n2 years experience\nLanguages\nFrench: fluent\nEnglish: fluent",
        "present": ["Python", "Django", "PostgreSQL"],
    },
    {
        "id": "cv_002",
        "text": "Candidate Synthétique Bêta\nbeta@fixture.invalid\nCOMPÉTENCES TECHNIQUES\nJava; Spring Boot; MySQL\n\nEXPÉRIENCE\n3 ans d'expérience\nFrançais: courant\nAnglais: intermédiaire",
        "present": ["Java", "Spring Boot", "MySQL"],
    },
    {
        "id": "cv_003",
        "text": "Synthetic Candidate Gamma\ngamma@fixture.invalid\nTECHNOLOGIES\nTypeScript | React | Node.js\n\nFORMATION\nSynthetic Institute\nJanuary 2020 - December 2021",
        "present": ["TypeScript", "React", "Node.js"],
    },
    {
        "id": "cv_004",
        "text": "Synthetic Candidate Delta\nSKILLS: Python, Python, Docker, Docker\n\nPROJECTS\nBuilt a deterministic fixture.",
        "present": ["Python", "Docker"],
    },
    {
        "id": "cv_005",
        "text": "Synthetic Candidate Epsilon\nEXPERIENCE\nChef de projet — Synthetic Example Team\nCoordinated delivery.\n\nEDUCATION\nSynthetic Institute",
        "absent": ["Chef"],
    },
    {
        "id": "cv_006",
        "text": "Synthetic Candidate Zeta\nSKILLS\nGo, R, Spring\n\nEXPERIENCE\nSynthetic work history.",
        "classification": "POLICY_PENDING",
    },
    {"id": "cv_007", "text": "", "present": [], "absent": ["Python"]},
    {
        "id": "cv_008",
        "kind": "pdf",
        "text": "Synthetic PDF Candidate\npdf.candidate@fixture.invalid\nSKILLS\nPython, SQLite\n\nEDUCATION\nSynthetic Institute",
        "present": ["Python", "SQLite"],
    },
)


MATCH_FIXTURES: tuple[dict[str, Any], ...] = (
    {"id": "match_001", "profile": ["Python"], "required": ["Python"], "optional": [], "label": "exact_skill_match"},
    {"id": "match_002", "profile": [], "required": ["Python"], "optional": [], "label": "missing_required_skill"},
    {"id": "match_003", "profile": ["Python"], "required": ["Python", "Django"], "optional": ["PostgreSQL"], "label": "partial_overlap"},
    {"id": "match_004", "profile": ["React"], "required": ["Python"], "optional": ["Django"], "label": "no_overlap"},
    {"id": "match_005", "profile": [".NET"], "profile_raw": [".NET Core"], "required": [".NET"], "optional": [], "label": "alias_identity_equivalence"},
    {"id": "match_006", "profile": ["Python", "Python"], "required": ["Python", "Python"], "optional": [], "label": "duplicate_profile_and_job_skill"},
    {"id": "match_007", "profile": [".NET"], "profile_raw": ["dotnet core"], "required": [".NET"], "optional": [], "label": "deprecated_replacement_behavior"},
    {"id": "match_008", "profile": ["Python"], "required": [], "optional": [], "label": "absent_match_state", "signal": "missing"},
    {"id": "match_009", "profile": ["Python"], "required": ["Python"], "optional": [], "label": "low_confidence_required", "confidence": "0.490"},
)


def _make_source() -> JobSource:
    return JobSource.objects.create(
        name="Synthetic Baseline Source",
        slug="synthetic-baseline-source",
        source_type=SourceType.FIXTURE,
        is_active=True,
    )


def _make_job(
    *,
    source: JobSource,
    index: int,
    title: str,
    description: str,
    required: list[str] | None = None,
    optional: list[str] | None = None,
    public_id: uuid.UUID | None = None,
    skill_signal_quality: str = "strong",
) -> NormalizedJob:
    source_job_id = f"synthetic-baseline-{index:03d}"
    raw = RawJobRecord.objects.create(
        source=source,
        source_job_id=source_job_id,
        raw_payload_json={},
        payload_hash=hashlib.sha256(source_job_id.encode("ascii")).hexdigest(),
        first_seen_at=FIXED_TIME,
        last_seen_at=FIXED_TIME,
        last_fetched_at=FIXED_TIME,
    )
    return NormalizedJob.objects.create(
        public_id=public_id or _fixed_uuid(0x10000000, index),
        source=source,
        raw_record=raw,
        source_job_id=source_job_id,
        title=title,
        company_name="Synthetic Example Labs",
        location="Synthetic City",
        country="FR",
        city="Synthetic City",
        contract_type="synthetic",
        remote_type=RemoteType.HYBRID,
        job_type=JobType.FULL_TIME_JOB,
        experience_level=ExperienceLevel.MID_LEVEL,
        description=description,
        status=JobStatus.ACTIVE,
        required_skills_json=required or [],
        optional_skills_json=optional or [],
        language_requirements_json={},
        classification_json={"family": "software_development", "is_it": True, "confidence": "high"},
        skill_signal_quality=skill_signal_quality,
        first_seen_at=FIXED_TIME,
        last_seen_at=FIXED_TIME,
        last_fetched_at=FIXED_TIME,
        published_at=FIXED_TIME,
    )


def _build_job_domain(source: JobSource, skills: dict[str, Skill]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    for index, fixture in enumerate(JOB_FIXTURES, start=1):
        classification = fixture.get("classification", "OBVIOUS_GOLD")
        synthetic_input = {
            "description": fixture["description"],
            "optional_skills": fixture.get("optional", []),
            "required_skills": fixture.get("required", []),
            "title": fixture["title"],
        }
        case = _case(
            case_id=fixture["id"],
            domain="job_extraction",
            classification=classification,
            synthetic_input=synthetic_input,
            expected_present=fixture.get("present", []),
            expected_absent=fixture.get("absent", []),
            skills=skills,
        )
        job = _make_job(
            source=source,
            index=index,
            title=fixture["title"],
            description=fixture["description"],
            required=fixture.get("required", []),
            optional=fixture.get("optional", []),
        )
        result = JobSkillExtractionService.extract_for_job(job)
        job.refresh_from_db()
        materialized = []
        for row in job.job_skills.select_related("skill").all():
            materialized.append(
                {
                    "canonical_name": row.skill.canonical_name,
                    "confidence": row.confidence,
                    "requirement_type": row.requirement_type,
                    "skill_uid": _skill_uid(row.skill),
                    "source": row.source,
                }
            )
        materialized.sort(key=lambda item: (item["skill_uid"], item["requirement_type"]))
        canonical_skills = sorted((_skill_record(skill) for skill in result.canonical_skills), key=lambda item: item["skill_uid"])
        outputs.append(
            {
                "case_id": fixture["id"],
                "canonical_skills": canonical_skills,
                "evidence_offsets_returned": False,
                "materialized_skills": materialized,
                "raw_candidates": sorted(result.raw_candidates, key=lambda value: (value.casefold(), value)),
                "skill_extraction_status": job.skill_extraction_status,
                "skill_signal_quality": job.skill_signal_quality,
            }
        )
        cases.append(case)
        job.status = JobStatus.ARCHIVED
        job.save(update_fields=["status"])
    return cases, outputs


def _build_canonical_domain(skills: dict[str, Skill]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    for fixture in CANONICAL_FIXTURES:
        classification = fixture.get("classification", "OBVIOUS_GOLD")
        case = _case(
            case_id=fixture["id"],
            domain="canonicalization",
            classification=classification,
            synthetic_input={"raw_skills": fixture["raw"]},
            expected_present=fixture.get("present", []),
            expected_absent=fixture.get("absent", []),
            skills=skills,
        )
        result = SkillNormalizerService.normalize_many(fixture["raw"], "manual")
        canonical_skills = sorted((_skill_record(skill) for skill in result.canonical_skills), key=lambda item: item["skill_uid"])
        unmatched = sorted(
            (
                {
                    "normalized_text": candidate.normalized_text,
                    "raw_skill_text": candidate.raw_skill_text,
                    "status": candidate.status,
                }
                for candidate in result.unmatched_candidates
            ),
            key=lambda item: (item["normalized_text"], item["raw_skill_text"]),
        )
        outputs.append(
            {
                "case_id": fixture["id"],
                "canonical_skills": canonical_skills,
                "unmatched_candidates": unmatched,
            }
        )
        cases.append(case)
    return cases, outputs


def _write_synthetic_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    try:
        page = document.new_page(width=595, height=842)
        result = page.insert_textbox(fitz.Rect(72, 72, 523, 770), text, fontsize=11)
        if result < 0:
            raise BaselineError("synthetic PDF fixture text did not fit")
        document.set_metadata({})
        document.save(path, garbage=4, deflate=True, clean=True)
    finally:
        document.close()


def _build_cv_domain(skills: dict[str, Skill], workspace: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    for fixture in CV_FIXTURES:
        classification = fixture.get("classification", "OBVIOUS_GOLD")
        input_kind = fixture.get("kind", "text")
        case = _case(
            case_id=fixture["id"],
            domain="cv_extraction",
            classification=classification,
            synthetic_input={"input_kind": "generated_born_digital_pdf" if input_kind == "pdf" else "synthetic_text", "text": fixture["text"]},
            expected_present=fixture.get("present", []),
            expected_absent=fixture.get("absent", []),
            skills=skills,
        )
        text_result = None
        raw_text = fixture["text"]
        if input_kind == "pdf":
            pdf_path = workspace / "synthetic-born-digital.pdf"
            _write_synthetic_pdf(pdf_path, raw_text)
            text_result = CVTextExtractionService.extract_from_path(str(pdf_path))
            if not text_result.get("success"):
                raise BaselineError("production PDF text extraction rejected the synthetic fixture")
            raw_text = text_result["raw_text"]
            pdf_path.unlink()
        result = CVDeterministicExtractorService.extract(raw_text)
        normalization = SkillNormalizerService.normalize_many(result.get("raw_skills", []), "cv")
        canonical_skills = sorted((_skill_record(skill) for skill in normalization.canonical_skills), key=lambda item: item["skill_uid"])
        output = {
            "case_id": fixture["id"],
            "canonical_skills": canonical_skills,
            "deterministic_output": result,
            "evidence_offsets_returned": False,
        }
        if text_result is not None:
            output["pdf_text_extraction"] = text_result
        if fixture["id"] == "cv_003":
            output["date_range_years_estimate"] = CVParsingService._estimate_years_from_text(raw_text)
        outputs.append(output)
        cases.append(case)
    return cases, outputs


def _make_profile(
    *,
    index: int,
    skill_names: list[str],
    raw_names: list[str] | None,
    skills: dict[str, Skill],
) -> CandidateProfile:
    User = get_user_model()
    user = User.objects.create(
        username=f"synthetic-match-{index:03d}",
        email=f"synthetic-match-{index:03d}@fixture.invalid",
    )
    profile = CandidateProfile.objects.create(
        user=user,
        public_id=_fixed_uuid(0x20000000, index),
        years_experience=Decimal("3.0"),
        current_level="mid_level",
        target_country="France",
        target_roles=["Backend Developer"],
        french_level="fluent",
        english_level="fluent",
        relocation_preference="yes",
        remote_preference="hybrid",
        profile_completion_score=80,
    )
    raw_names = raw_names or skill_names
    for position, name in enumerate(skill_names):
        raw_name = raw_names[min(position, len(raw_names) - 1)]
        normalized = normalize_skill_text(raw_name)
        if ProfileSkill.objects.filter(profile=profile, normalized_name=normalized).exists():
            normalized = f"{normalized}-duplicate-{position}"
        ProfileSkill.objects.create(
            profile=profile,
            skill=skills[name],
            raw_name=raw_name,
            normalized_name=normalized,
            source="synthetic_baseline",
            confidence=100,
            is_confirmed=True,
        )
    return profile


def _score_output(result: Any, skills: dict[str, Skill]) -> dict[str, Any]:
    values = asdict(result)
    values.pop("recommended_actions", None)
    by_name = skills

    def convert(items: list[dict[str, str]]) -> list[dict[str, str]]:
        converted = []
        for item in items:
            skill = by_name[item["name"]]
            converted.append({**item, "skill_uid": _skill_uid(skill)})
        return sorted(converted, key=lambda item: (item["skill_uid"], item.get("type", item.get("requirement_type", ""))))

    values["strong_skills"] = convert(values["strong_skills"])
    values["missing_required_skills"] = convert(values["missing_required_skills"])
    values["missing_optional_skills"] = convert(values["missing_optional_skills"])
    return values


def _build_matching_domain(source: JobSource, skills: dict[str, Skill]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    offset = 200
    for index, fixture in enumerate(MATCH_FIXTURES, start=1):
        profile = _make_profile(
            index=index,
            skill_names=fixture["profile"],
            raw_names=fixture.get("profile_raw"),
            skills=skills,
        )
        job = _make_job(
            source=source,
            index=offset + index,
            public_id=_fixed_uuid(0x30000000, index),
            title="Synthetic Backend Developer",
            description="Synthetic backend systems role.",
            required=fixture["required"],
            optional=fixture["optional"],
            skill_signal_quality=fixture.get("signal", "strong"),
        )
        confidence = Decimal(fixture.get("confidence", "1.000"))
        for position, name in enumerate(fixture["required"]):
            NormalizedJobSkill.objects.create(
                job=job,
                skill=skills[name],
                requirement_type=RequirementType.REQUIRED if position == 0 or fixture["label"] != "duplicate_profile_and_job_skill" else RequirementType.OPTIONAL,
                source=SkillSource.RULE,
                confidence=confidence,
            )
        for name in fixture["optional"]:
            if NormalizedJobSkill.objects.filter(job=job, skill=skills[name], requirement_type=RequirementType.OPTIONAL).exists():
                continue
            NormalizedJobSkill.objects.create(
                job=job,
                skill=skills[name],
                requirement_type=RequirementType.OPTIONAL,
                source=SkillSource.RULE,
                confidence=Decimal("1.000"),
            )
        case = {
            "case_id": fixture["id"],
            "classification": "CURRENT_OBSERVATION",
            "domain": "matching_recommendation",
            "synthetic_input": {
                "job_public_id": str(job.public_id),
                "label": fixture["label"],
                "optional_skill_uids": _uids(fixture["optional"], skills),
                "profile_public_id": str(profile.public_id),
                "profile_skill_uids": _uids(fixture["profile"], skills),
                "required_skill_uids": _uids(fixture["required"], skills),
            },
        }
        score = MatchScoringService.calculate(profile, job)
        outputs.append({"case_id": fixture["id"], "score": _score_output(score, skills)})
        cases.append(case)
        job.status = JobStatus.ARCHIVED
        job.save(update_fields=["status"])

    ranking_index = 10
    ranking_profile = _make_profile(index=ranking_index, skill_names=["Python"], raw_names=None, skills=skills)
    ranking_jobs = []
    for position, title in enumerate(("Alpha Python Developer", "Beta Python Developer", "Gamma Django Developer"), start=1):
        job = _make_job(
            source=source,
            index=offset + 50 + position,
            public_id=_fixed_uuid(0x30000000, 50 + position),
            title=title,
            description="Synthetic deterministic ranking role.",
            required=["Python"] if position < 3 else ["Django"],
            optional=[],
        )
        skill = skills["Python"] if position < 3 else skills["Django"]
        NormalizedJobSkill.objects.create(
            job=job,
            skill=skill,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.RULE,
            confidence=Decimal("1.000"),
        )
        ranking_jobs.append(job)

    recommendation_result = RecommendationService.refresh_for_user(ranking_profile.user, "manual_admin")
    rows = list(JobRecommendation.objects.filter(user=ranking_profile.user, status="active").select_related("job").order_by("rank"))
    ranking_case = {
        "case_id": "match_010",
        "classification": "CURRENT_OBSERVATION",
        "domain": "matching_recommendation",
        "synthetic_input": {
            "job_public_ids": sorted(str(job.public_id) for job in ranking_jobs),
            "label": "deterministic_recommendation_tie_ordering",
            "profile_public_id": str(ranking_profile.public_id),
            "profile_skill_uids": _uids(["Python"], skills),
        },
    }
    ranking_output = {
        "case_id": "match_010",
        "recommendation_counts": {
            "candidate_jobs": recommendation_result.candidate_jobs_count,
            "scored_jobs": recommendation_result.scored_jobs_count,
            "stored_recommendations": recommendation_result.stored_recommendations_count,
        },
        "recommendation_order": [
            {
                "fit_score": row.fit_score,
                "job_public_id": str(row.job.public_id),
                "rank": row.rank,
                "ranking_score": row.ranking_score,
            }
            for row in rows
        ],
    }
    cases.append(ranking_case)
    outputs.append(ranking_output)
    return cases, outputs


def _observed_uids(output: dict[str, Any]) -> set[str]:
    return {item["skill_uid"] for item in output.get("canonical_skills", [])}


def _metrics(cases: list[dict[str, Any]], outputs_by_domain: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    outputs = {
        output["case_id"]: output
        for domain_outputs in outputs_by_domain.values()
        for output in domain_outputs
    }
    classifications = {name: 0 for name in sorted(CLASSIFICATIONS)}
    domain_counts = {domain: 0 for domain in DOMAIN_FILES}
    tp = fp = fn = tn = 0
    obvious_assertions = 0
    for case in cases:
        classifications[case["classification"]] += 1
        domain_counts[case["domain"]] += 1
        if case["classification"] != "OBVIOUS_GOLD":
            continue
        output = outputs[case["case_id"]]
        observed = _observed_uids(output)
        present = set(case.get("expected_present_skill_uids", []))
        absent = set(case.get("expected_absent_skill_uids", []))
        tp += len(present & observed)
        fn += len(present - observed)
        fp += len(absent & observed)
        tn += len(absent - observed)
        obvious_assertions += len(present) + len(absent)

    precision = None if tp + fp == 0 else _decimal_string((Decimal(tp) / Decimal(tp + fp)).quantize(Decimal("0.000001")))
    recall = None if tp + fn == 0 else _decimal_string((Decimal(tp) / Decimal(tp + fn)).quantize(Decimal("0.000001")))
    return {
        "baseline_version": BASELINE_VERSION,
        "case_counts_by_classification": classifications,
        "case_counts_by_domain": domain_counts,
        "deterministic_reproduction": {
            "pass_count": len(cases),
            "total_count": len(cases),
        },
        "known_failure_count": 0,
        "metric_scope": "Skill-presence assertions from OBVIOUS_GOLD cases only; POLICY_PENDING and CURRENT_OBSERVATION cases are excluded.",
        "obvious_gold_skill_assertions": {
            "false_negatives": fn,
            "false_positives": fp,
            "precision": precision,
            "recall": recall,
            "total_assertions": obvious_assertions,
            "true_negatives": tn,
            "true_positives": tp,
        },
        "policy_pending_count": classifications["POLICY_PENDING"],
        "runtime_benchmarks_included": False,
    }


def _known_failures(
    cases: list[dict[str, Any]],
    outputs_by_domain: dict[str, list[dict[str, Any]]],
    skills: dict[str, Skill],
) -> list[dict[str, str]]:
    outputs = {output["case_id"]: output for output in outputs_by_domain["job_extraction"]}
    entries: list[dict[str, str]] = []
    known_specs = (
        ("job_017", "React", True, "hard_negative_false_positive", "Ordinary verb usage materialized the React framework."),
        ("job_021", "Go", False, "catalog_positive_false_negative", "The catalog-positive Go language context was not materialized."),
        ("job_023", "R", False, "catalog_positive_false_negative", "The catalog-positive R language context was not materialized."),
        ("job_033", "Tableau", True, "hard_negative_false_positive", "The ordinary French noun materialized the Tableau product."),
    )
    for case_id, skill_name, failure_when_present, category, summary in known_specs:
        observed = _skill_uid(skills[skill_name]) in _observed_uids(outputs[case_id])
        failed = observed if failure_when_present else not observed
        if failed:
            entries.append(
                {
                    "case_id": case_id,
                    "classification": "OBVIOUS_GOLD",
                    "current_observation": summary,
                    "domain": "job_extraction",
                    "failure_category": category,
                    "policy_status": "known_failure",
                    "safe_summary": summary,
                }
            )
    for case in cases:
        if case["classification"] != "POLICY_PENDING":
            continue
        output = next(
            output
            for domain_outputs in outputs_by_domain.values()
            for output in domain_outputs
            if output["case_id"] == case["case_id"]
        )
        observed_names = [item["canonical_name"] for item in output.get("canonical_skills", [])]
        observation = "Current canonical skills: " + (", ".join(sorted(observed_names)) if observed_names else "none")
        entries.append(
            {
                "case_id": case["case_id"],
                "classification": "POLICY_PENDING",
                "current_observation": observation,
                "domain": case["domain"],
                "failure_category": "ambiguity_policy_not_frozen",
                "policy_status": "policy_pending",
                "safe_summary": "The current output is recorded without selecting a desired final ambiguity policy.",
            }
        )
    return sorted(entries, key=lambda item: item["case_id"])


def _module_hashes() -> dict[str, str]:
    values = {}
    for relative in SERVICE_MODULES:
        path = ROOT / relative
        if not path.is_file():
            raise BaselineError(f"service module missing: {relative}")
        values[relative] = sha256_file(path)
    return values


def _content_digest(file_sha256: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(file_sha256):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256[name].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def reset_synthetic_state() -> None:
    User = get_user_model()
    JobRecommendation.objects.all().delete()
    RecommendationRun.objects.all().delete()
    MatchResult.objects.all().delete()
    NormalizedJob.objects.all().delete()
    RawJobRecord.objects.all().delete()
    JobSource.objects.all().delete()
    UnmatchedSkillCandidate.objects.all().delete()
    User.objects.filter(username__startswith="synthetic-").delete()


@contextmanager
def external_calls_forbidden():
    refusal = AssertionError("deterministic baseline forbids LLM and external calls")
    with ExitStack() as stack:
        stack.enter_context(patch("urllib.request.urlopen", side_effect=refusal))
        stack.enter_context(patch("http.client.HTTPConnection.request", side_effect=refusal))
        stack.enter_context(patch("http.client.HTTPSConnection.request", side_effect=refusal))
        stack.enter_context(patch("apps.llm.services.client.OpenRouterClient._make_request", side_effect=refusal))
        stack.enter_context(patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers", side_effect=refusal))
        stack.enter_context(patch("apps.jobs.services.france_travail.client.FranceTravailClient.get_offer_detail", side_effect=refusal))
        yield


def build_bundle(output_dir: Path, *, django_commit: str, django_branch: str = "dev") -> dict[str, Any]:
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise BaselineError("bundle build target already exists")
    if not isinstance(django_commit, str) or len(django_commit) != 40 or any(char not in "0123456789abcdef" for char in django_commit):
        raise BaselineError("django_commit must be 40 lowercase hexadecimal characters")
    if django_branch != "dev":
        raise BaselineError("the baseline source branch must be dev")
    if connection.settings_dict.get("NAME") == settings.DATABASES["default"].get("NAME") and not str(connection.settings_dict.get("NAME", "")).startswith("test_"):
        raise BaselineError("baseline build requires an isolated Django test database")
    if settings.LLM_ENABLED or settings.JOB_ENRICHMENT_ENABLED or settings.CV_LLM_EXTRACTION_ENABLED:
        raise BaselineError("LLM and enrichment settings must be disabled")

    output_dir.mkdir(parents=True, mode=0o700)
    workspace = Path(tempfile.mkdtemp(prefix="tuniatlas-baseline-work-"))
    try:
        reset_synthetic_state()
        SkillSeedService.seed_initial_taxonomy()
        skills = _skill_map()
        source = _make_source()
        with external_calls_forbidden():
            job_cases, job_outputs = _build_job_domain(source, skills)
            canonical_cases, canonical_outputs = _build_canonical_domain(skills)
            cv_cases, cv_outputs = _build_cv_domain(skills, workspace)
            matching_cases, matching_outputs = _build_matching_domain(source, skills)

        cases = sorted(job_cases + canonical_cases + cv_cases + matching_cases, key=lambda item: item["case_id"])
        outputs_by_domain = {
            "job_extraction": sorted(job_outputs, key=lambda item: item["case_id"]),
            "cv_extraction": sorted(cv_outputs, key=lambda item: item["case_id"]),
            "canonicalization": sorted(canonical_outputs, key=lambda item: item["case_id"]),
            "matching_recommendation": sorted(matching_outputs, key=lambda item: item["case_id"]),
        }
        known_failures = _known_failures(cases, outputs_by_domain, skills)
        metrics = _metrics(cases, outputs_by_domain)
        metrics["known_failure_count"] = sum(item["policy_status"] == "known_failure" for item in known_failures)

        readme = (
            "TuniAtlas ML-0 deterministic baseline\n"
            "\n"
            "Synthetic fixtures only. Current service observations are frozen without changing product behavior.\n"
            "POLICY_PENDING cases are excluded from obvious-gold metrics. No latency or hardware claim is included.\n"
        ).encode("utf-8")
        payloads: dict[str, bytes] = {
            "README.txt": readme,
            "cases.json": canonical_json_bytes({"baseline_version": BASELINE_VERSION, "cases": cases}),
            "job_extraction.json": canonical_json_bytes({"baseline_version": BASELINE_VERSION, "domain": "job_extraction", "outputs": outputs_by_domain["job_extraction"]}),
            "cv_extraction.json": canonical_json_bytes({"baseline_version": BASELINE_VERSION, "domain": "cv_extraction", "outputs": outputs_by_domain["cv_extraction"]}),
            "canonicalization.json": canonical_json_bytes({"baseline_version": BASELINE_VERSION, "domain": "canonicalization", "outputs": outputs_by_domain["canonicalization"]}),
            "matching_recommendation.json": canonical_json_bytes({"baseline_version": BASELINE_VERSION, "domain": "matching_recommendation", "outputs": outputs_by_domain["matching_recommendation"]}),
            "metrics.json": canonical_json_bytes(metrics),
            "known_failures.json": canonical_json_bytes({"baseline_version": BASELINE_VERSION, "entries": known_failures}),
        }
        payload_hashes = {name: sha256_bytes(value) for name, value in payloads.items()}
        bundle_content_sha256 = _content_digest(payload_hashes)
        manifest = {
            "baseline_format": BASELINE_FORMAT,
            "baseline_version": BASELINE_VERSION,
            "bundle_content_sha256": bundle_content_sha256,
            "case_counts": metrics["case_counts_by_domain"],
            "django_branch": django_branch,
            "django_commit": django_commit,
            "django_repository": "TaouaiB/tunitech-abroad",
            "exporter_contract_version": EXPORTER_CONTRACT_VERSION,
            "file_sha256": payload_hashes,
            "known_failure_counts": {
                "known_failure": metrics["known_failure_count"],
                "policy_pending": metrics["policy_pending_count"],
            },
            "output_counts": {domain: len(outputs) for domain, outputs in outputs_by_domain.items()},
            "service_module_hashes": _module_hashes(),
            "source_product": "TuniAtlas Jobs",
            "taxonomy_manifest_sha256": TAXONOMY_MANIFEST_SHA256,
            "taxonomy_snapshot_sha256": TAXONOMY_SNAPSHOT_SHA256,
            "taxonomy_version": TAXONOMY_VERSION,
        }
        payloads["manifest.json"] = canonical_json_bytes(manifest)
        for name, value in payloads.items():
            (output_dir / name).write_bytes(value)
        sums = "".join(f"{sha256_bytes(payloads[name])}  {name}\n" for name in sorted(payloads))
        (output_dir / "SHA256SUMS").write_text(sums, encoding="ascii", newline="\n")
        actual = tuple(sorted(path.name for path in output_dir.iterdir() if path.is_file()))
        if actual != tuple(sorted(EXPECTED_FILES)):
            raise BaselineError(f"built file set differs: {actual}")
        return manifest
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def compare_bundles(left: Path, right: Path) -> bool:
    left_files = sorted(path.name for path in left.iterdir() if path.is_file()) if left.is_dir() else []
    right_files = sorted(path.name for path in right.iterdir() if path.is_file()) if right.is_dir() else []
    return left_files == right_files == sorted(EXPECTED_FILES) and all((left / name).read_bytes() == (right / name).read_bytes() for name in left_files)


def publish_bundle(target: Path, builder: Callable[[Path], dict[str, Any]]) -> tuple[dict[str, Any], str]:
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    staging.rmdir()
    try:
        manifest = builder(staging)
        if target.exists():
            if not target.is_dir() or not compare_bundles(staging, target):
                raise BaselineError("existing baseline target is incomplete, has extras, or differs")
            shutil.rmtree(staging)
            return manifest, "idempotent"
        os.replace(staging, target)
        return manifest, "published"
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
