"""Test-only loader for the approved private ML-0 taxonomy snapshot."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.db import transaction

from apps.skills.models import Skill, SkillAlias


TAXONOMY_VERSION = "sha256:d6d5aebf5e4b958f163d2f33b8d441a36e6d638ac8c92379f18e6ebd40e2fc05"
TAXONOMY_SNAPSHOT_SHA256 = "f71e1a67420bebe00fe45ccb01ae508e5605178ce78bd9e5305780a0a93a002d"
TAXONOMY_MANIFEST_SHA256 = "0d410a706a19f05fa73b234bcd262ec8f85bf330c26fa3032295391e3ac09045"
EXPECTED_REGISTRY_COUNT = 522
EXPECTED_SNAPSHOT_SKILL_COUNT = 523
EXPECTED_ACTIVE_COUNT = 522
EXPECTED_INACTIVE_COUNT = 1
EXPECTED_ALIAS_COUNT = 863
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SKILL_KEYS = {
    "aliases",
    "canonical_name",
    "category",
    "deprecation",
    "esco_uri",
    "is_active",
    "skill_uid",
    "slug",
    "source",
}
ALIAS_KEYS = {"alias", "language", "normalized_alias"}
DEPRECATION_KEYS = {"reason", "replacement_skill_uid", "status"}


class SnapshotTaxonomyError(ValueError):
    """A controlled snapshot loading or equality failure."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _strict_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SnapshotTaxonomyError(f"{field} must be an integer")
    return value


def _uuid4(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise SnapshotTaxonomyError(f"{field} must be a UUIDv4 string")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise SnapshotTaxonomyError(f"{field} must be a UUIDv4 string") from exc
    if parsed.version != 4 or str(parsed) != value:
        raise SnapshotTaxonomyError(f"{field} must be a canonical lowercase UUIDv4 string")
    return value


@dataclass(frozen=True)
class SnapshotRegistry:
    skills: tuple[dict[str, Any], ...]
    registry_count: int
    active_count: int
    inactive_count: int
    alias_count: int
    registry_digest: str


def read_approved_snapshot(snapshot_dir: Path) -> SnapshotRegistry:
    root = Path(snapshot_dir).resolve()
    expected_files = {"README.txt", "SHA256SUMS", "manifest.json", "taxonomy.json"}
    if not root.is_dir() or {path.name for path in root.iterdir()} != expected_files:
        raise SnapshotTaxonomyError("approved taxonomy snapshot has the wrong file set")
    taxonomy_path = root / "taxonomy.json"
    manifest_path = root / "manifest.json"
    if _sha256(taxonomy_path) != TAXONOMY_SNAPSHOT_SHA256:
        raise SnapshotTaxonomyError("approved taxonomy snapshot checksum differs")
    if _sha256(manifest_path) != TAXONOMY_MANIFEST_SHA256:
        raise SnapshotTaxonomyError("approved taxonomy manifest checksum differs")
    try:
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SnapshotTaxonomyError("approved taxonomy snapshot is unreadable") from exc

    if not isinstance(taxonomy, dict) or not isinstance(manifest, dict):
        raise SnapshotTaxonomyError("approved taxonomy payloads must be objects")
    if taxonomy.get("taxonomy_version") != TAXONOMY_VERSION or manifest.get("taxonomy_version") != TAXONOMY_VERSION:
        raise SnapshotTaxonomyError("approved taxonomy version differs")
    counts = {
        "registry": _strict_int(manifest.get("registry_count"), "registry_count"),
        "skills": _strict_int(taxonomy.get("skill_count"), "skill_count"),
        "active": _strict_int(taxonomy.get("active_skill_count"), "active_skill_count"),
        "inactive": _strict_int(taxonomy.get("deprecated_skill_count"), "deprecated_skill_count"),
        "aliases": _strict_int(manifest.get("alias_count"), "alias_count"),
    }
    expected_counts = {
        "registry": EXPECTED_REGISTRY_COUNT,
        "skills": EXPECTED_SNAPSHOT_SKILL_COUNT,
        "active": EXPECTED_ACTIVE_COUNT,
        "inactive": EXPECTED_INACTIVE_COUNT,
        "aliases": EXPECTED_ALIAS_COUNT,
    }
    if counts != expected_counts:
        raise SnapshotTaxonomyError(f"approved taxonomy counts differ: {counts}")

    raw_skills = taxonomy.get("skills")
    if not isinstance(raw_skills, list) or len(raw_skills) != EXPECTED_SNAPSHOT_SKILL_COUNT:
        raise SnapshotTaxonomyError("approved taxonomy skills array differs")
    skill_uids: set[str] = set()
    canonical_names: set[str] = set()
    slugs: set[str] = set()
    normalized_aliases: set[str] = set()
    validated: list[dict[str, Any]] = []
    active_count = alias_count = 0
    for index, raw in enumerate(raw_skills):
        if not isinstance(raw, dict) or set(raw) != SKILL_KEYS:
            raise SnapshotTaxonomyError(f"skill[{index}] key contract differs")
        uid = _uuid4(raw["skill_uid"], f"skill[{index}].skill_uid")
        for field in ("canonical_name", "slug", "category", "source"):
            if not isinstance(raw[field], str) or not raw[field]:
                raise SnapshotTaxonomyError(f"skill[{index}].{field} is invalid")
        if not isinstance(raw["is_active"], bool):
            raise SnapshotTaxonomyError(f"skill[{index}].is_active is invalid")
        if raw["esco_uri"] is not None and not isinstance(raw["esco_uri"], str):
            raise SnapshotTaxonomyError(f"skill[{index}].esco_uri is invalid")
        deprecation = raw["deprecation"]
        if deprecation is not None:
            if not isinstance(deprecation, dict) or set(deprecation) != DEPRECATION_KEYS:
                raise SnapshotTaxonomyError(f"skill[{index}].deprecation is invalid")
            _uuid4(deprecation["replacement_skill_uid"], f"skill[{index}].replacement_skill_uid")
            if deprecation["status"] != "deprecated" or not isinstance(deprecation["reason"], str):
                raise SnapshotTaxonomyError(f"skill[{index}].deprecation values differ")
        if raw["is_active"] == (deprecation is not None):
            raise SnapshotTaxonomyError(f"skill[{index}] active/deprecation mapping differs")
        aliases = raw["aliases"]
        if not isinstance(aliases, list):
            raise SnapshotTaxonomyError(f"skill[{index}].aliases is invalid")
        previous_alias: tuple[str, str, str] | None = None
        for alias_index, alias in enumerate(aliases):
            if not isinstance(alias, dict) or set(alias) != ALIAS_KEYS:
                raise SnapshotTaxonomyError(f"skill[{index}].aliases[{alias_index}] differs")
            if not all(isinstance(alias[field], str) and alias[field] for field in ALIAS_KEYS):
                raise SnapshotTaxonomyError(f"skill[{index}].aliases[{alias_index}] is invalid")
            alias_key = (alias["normalized_alias"], alias["alias"], alias["language"])
            if previous_alias is not None and alias_key <= previous_alias:
                raise SnapshotTaxonomyError(f"skill[{index}] aliases are not strictly ordered")
            previous_alias = alias_key
            if alias["normalized_alias"] in normalized_aliases:
                raise SnapshotTaxonomyError("duplicate normalized alias in approved snapshot")
            normalized_aliases.add(alias["normalized_alias"])
            alias_count += 1
        if uid in skill_uids or raw["canonical_name"] in canonical_names or raw["slug"] in slugs:
            raise SnapshotTaxonomyError("duplicate skill identity in approved snapshot")
        skill_uids.add(uid)
        canonical_names.add(raw["canonical_name"])
        slugs.add(raw["slug"])
        active_count += int(raw["is_active"])
        validated.append(raw)

    if active_count != EXPECTED_ACTIVE_COUNT or alias_count != EXPECTED_ALIAS_COUNT:
        raise SnapshotTaxonomyError("approved taxonomy record counts do not reconcile")
    canonical = sorted(validated, key=lambda item: item["skill_uid"])
    if validated != canonical:
        raise SnapshotTaxonomyError("approved taxonomy skills are not ordered by skill_uid")
    registry_digest = hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()
    if not SHA256_RE.fullmatch(registry_digest):
        raise SnapshotTaxonomyError("taxonomy registry digest is invalid")
    return SnapshotRegistry(
        skills=tuple(canonical),
        registry_count=EXPECTED_REGISTRY_COUNT,
        active_count=EXPECTED_ACTIVE_COUNT,
        inactive_count=EXPECTED_INACTIVE_COUNT,
        alias_count=EXPECTED_ALIAS_COUNT,
        registry_digest=registry_digest,
    )


def _database_records(snapshot: SnapshotRegistry) -> list[dict[str, Any]]:
    deprecations = {item["skill_uid"]: item["deprecation"] for item in snapshot.skills}
    records = []
    for skill in Skill.objects.prefetch_related("aliases").order_by("skill_uid"):
        aliases = sorted(
            (
                {
                    "alias": alias.alias,
                    "language": alias.language,
                    "normalized_alias": alias.normalized_alias,
                }
                for alias in skill.aliases.all()
            ),
            key=lambda item: (item["normalized_alias"], item["alias"], item["language"]),
        )
        uid = str(skill.skill_uid)
        records.append(
            {
                "aliases": aliases,
                "canonical_name": skill.canonical_name,
                "category": skill.category,
                "deprecation": deprecations.get(uid),
                "esco_uri": skill.esco_uri,
                "is_active": skill.is_active,
                "skill_uid": uid,
                "slug": skill.slug,
                "source": skill.source,
            }
        )
    return records


def prove_database_equality(snapshot: SnapshotRegistry) -> None:
    records = _database_records(snapshot)
    if records != list(snapshot.skills):
        raise SnapshotTaxonomyError("isolated test database taxonomy differs from approved snapshot")
    active = sum(item["is_active"] for item in records)
    aliases = sum(len(item["aliases"]) for item in records)
    if len(records) != EXPECTED_SNAPSHOT_SKILL_COUNT:
        raise SnapshotTaxonomyError("isolated test database canonical skill count differs")
    if active != snapshot.active_count or len(records) - active != snapshot.inactive_count:
        raise SnapshotTaxonomyError("isolated test database active/inactive mapping differs")
    if aliases != snapshot.alias_count:
        raise SnapshotTaxonomyError("isolated test database alias count differs")
    digest = hashlib.sha256(_canonical_json_bytes(records)).hexdigest()
    if digest != snapshot.registry_digest:
        raise SnapshotTaxonomyError("isolated test database registry digest differs")


@transaction.atomic
def populate_test_database(snapshot_dir: Path) -> SnapshotRegistry:
    snapshot = read_approved_snapshot(snapshot_dir)
    SkillAlias.objects.all().delete()
    Skill.objects.all().delete()
    Skill.objects.bulk_create(
        [
            Skill(
                skill_uid=uuid.UUID(item["skill_uid"]),
                canonical_name=item["canonical_name"],
                slug=item["slug"],
                category=item["category"],
                is_active=item["is_active"],
                source=item["source"],
                esco_uri=item["esco_uri"],
            )
            for item in snapshot.skills
        ]
    )
    by_uid = {str(skill.skill_uid): skill for skill in Skill.objects.all()}
    SkillAlias.objects.bulk_create(
        [
            SkillAlias(
                skill=by_uid[item["skill_uid"]],
                alias=alias["alias"],
                normalized_alias=alias["normalized_alias"],
                language=alias["language"],
            )
            for item in snapshot.skills
            for alias in item["aliases"]
        ]
    )
    prove_database_equality(snapshot)
    return snapshot
