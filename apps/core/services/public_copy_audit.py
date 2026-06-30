import os
from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class PublicCopyViolation:
    path: str
    line: int
    phrase: str


class PublicCopyAuditService:
    FORBIDDEN_PHRASES = [
        "france only",
        "france-only",
        "france first",
        "france-first",
        "france it jobs",
        "france opportunities",
        "france recruiters",
        "french market only",
        "objectif france",
        "offres françaises",
        "offres françaises actualisées",
        "offres it françaises",
        "offres en france",
        "offres d'emploi en france",
        "offres it en france",
    ]

    ALLOWED_CONTEXTS = [
        "france travail",
        "source_slug",
        "source_url",
        "job.location",
        "job.country",
        "job_snapshot_json.country",
        "job_snapshot_json.location",
    ]

    @classmethod
    def find_forbidden_terms(cls, paths: list[str] | None = None) -> dict:
        scan_paths = paths or [
            os.path.join(settings.BASE_DIR, "templates"),
            os.path.join(settings.BASE_DIR, "apps"),
        ]
        violations: list[PublicCopyViolation] = []

        for scan_path in scan_paths:
            for path in cls._iter_template_paths(scan_path):
                with open(path, "r", encoding="utf-8") as handle:
                    for line_num, line in enumerate(handle, 1):
                        lower_line = line.lower()
                        if cls._is_allowed_context(lower_line):
                            continue
                        for phrase in cls.FORBIDDEN_PHRASES:
                            if phrase in lower_line:
                                violations.append(PublicCopyViolation(path, line_num, phrase))

        return {
            "ok": not violations,
            "service": "public_copy_audit",
            "counts": {"violations": len(violations)},
            "violations": [
                {"path": item.path, "line": item.line, "phrase": item.phrase}
                for item in violations
            ],
        }

    @classmethod
    def _iter_template_paths(cls, scan_path: str):
        if os.path.isfile(scan_path):
            if scan_path.endswith(".html"):
                yield scan_path
            return

        for root, dirs, files in os.walk(scan_path):
            if "admin" in root.split(os.sep):
                continue
            for file_name in files:
                if file_name.endswith(".html"):
                    yield os.path.join(root, file_name)

    @classmethod
    def _is_allowed_context(cls, lower_line: str) -> bool:
        return any(context in lower_line for context in cls.ALLOWED_CONTEXTS)
