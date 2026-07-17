"""Deterministic skill taxonomy snapshot exporter.

The exporter is the Django-side mirror of the ML repository taxonomy
consumer. It produces an immutable, byte-for-byte reproducible snapshot
of the canonical registry skills together with the explicitly
deprecated legacy identities.

The export format is intentionally minimal for this ML-0 gate. A formal
JSON Schema for taxonomy snapshots belongs to ML-1 and must not be
created here.

Format::

    format_name: tuniatlas_skill_taxonomy_snapshot
    format_version: 1

The exporter MUST:

* read the canonical registry through the existing registry service;
* read ``Skill`` and ``SkillAlias`` through the Django ORM;
* exclude the known invalid taxonomy artifact ``Langues non précisées``;
* export the deprecated ``.NET Core`` identity when it exists, with
  replacement pointing to ``.NET``;
* never embed internal database integer IDs;
* produce deterministic JSON output for an unchanged taxonomy;
* prove the source-state invariants (registry coverage, invalid
  artifact state, deprecated identity state, exact counts) before any
  staging write;
* write and verify every file only inside a staging directory that
  lives under the final output root, on the same filesystem;
* publish the complete four-file directory with a single atomic
  filesystem rename/replace operation;
* treat an existing byte-identical snapshot as idempotent success;
* refuse to overwrite a differing or incomplete existing snapshot;
* never leave a partial target directory or a stale staging directory
  on failure;
* return only sanitized metadata.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from django.db import transaction

from apps.skills.models import Skill, SkillAlias
from apps.skills.services import skill_uid_registry


SNAPSHOT_FORMAT_NAME = "tuniatlas_skill_taxonomy_snapshot"
SNAPSHOT_FORMAT_VERSION = 1
SNAPSHOT_FILENAME = "taxonomy.json"
MANIFEST_FILENAME = "manifest.json"
README_FILENAME = "README.txt"
SHASUMS_FILENAME = "SHA256SUMS"

EXPORTER_CONTRACT_VERSION = "ml0-v1"

INVALID_ARTIFACT_CANONICAL_NAME = "Langues non précisées"
# Tombstone UUID for the invalid artifact row. The contract pins this
# exact value so that downstream consumers and tests can recognize the
# row even when it is excluded from the snapshot payload.
INVALID_ARTIFACT_TOMBSTONE_UUID = uuid.UUID("0b71fefd-ea81-42e1-a4e1-2d84d3497960")
DEPRECATED_DOTNET_CORE_CANONICAL_NAME = ".NET Core"
DOTNET_CANONICAL_NAME = ".NET"

# Expected ML-0 source-state counts. These are exact: any deviation
# (missing registry row, extra non-registry row, extra deprecated row,
# unexpected invalid-artifact state) must fail the exporter before any
# staging write.
EXPECTED_REGISTRY_COUNT = 522
EXPECTED_ACTIVE_SKILL_COUNT = EXPECTED_REGISTRY_COUNT
EXPECTED_DEPRECATED_SKILL_COUNT = 1
EXPECTED_TOTAL_SKILL_COUNT = EXPECTED_ACTIVE_SKILL_COUNT + EXPECTED_DEPRECATED_SKILL_COUNT

REQUIRED_SKILL_FIELDS = (
    "skill_uid",
    "canonical_name",
    "slug",
    "category",
    "is_active",
    "source",
    "esco_uri",
    "aliases",
    "deprecation",
)

REQUIRED_ALIAS_FIELDS = (
    "alias",
    "normalized_alias",
    "language",
)

REQUIRED_MANIFEST_FIELDS = (
    "manifest_format",
    "manifest_version",
    "taxonomy_version",
    "taxonomy_content_sha256",
    "snapshot_filename",
    "snapshot_sha256",
    "source_product",
    "source_repository",
    "source_commit",
    "source_branch",
    "source_skills_migration",
    "registry_count",
    "snapshot_skill_count",
    "active_skill_count",
    "deprecated_skill_count",
    "alias_count",
    "excluded_invalid_artifacts",
    "exporter_contract_version",
)

FORBIDDEN_TOP_LEVEL_FIELDS = (
    "id",
    "pk",
    "skill_id",
    "created_at",
    "updated_at",
    "generated_at",
    "timestamp",
    "exported_at",
)

EXCLUDED_INVALID_ARTIFACTS = (INVALID_ARTIFACT_CANONICAL_NAME,)

# Required migration to be applied on the source database.
REQUIRED_SOURCE_MIGRATION = "skills.0004_skill_skill_uid_finalize"
REQUIRED_SOURCE_MIGRATION_APP = "skills"

STAGING_DIR_PREFIX = ".taxonomy-snapshot-staging-"

# Source commit shape: lowercase hex SHA-1 of exactly 40 characters.
SOURCE_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class TaxonomySnapshotError(Exception):
    """Base class for exporter errors."""


class TaxonomySnapshotContractError(TaxonomySnapshotError):
    """The taxonomy does not satisfy the exporter contract."""


class TaxonomySnapshotEnvironmentError(TaxonomySnapshotError):
    """The Django environment does not satisfy the gate."""


class TaxonomySnapshotPublishError(TaxonomySnapshotError):
    """Atomic publish of the snapshot failed."""


@dataclasses.dataclass(frozen=True)
class TaxonomySnapshotResult:
    """Sanitized exporter result.

    This is the only object the management command returns or prints.
    It must never contain snapshot contents, private text, or database
    integer IDs.
    """

    taxonomy_version: str
    snapshot_dir: str
    taxonomy_content_sha256: str
    snapshot_file_sha256: str
    manifest_sha256: str
    readme_sha256: str
    skill_count: int
    active_skill_count: int
    deprecated_skill_count: int
    alias_count: int
    registry_count: int
    excluded_invalid_artifacts: Tuple[str, ...]
    idempotent: bool
    source_commit: str
    source_branch: str

    def to_public_dict(self) -> dict:
        return {
            "taxonomy_version": self.taxonomy_version,
            "snapshot_dir": self.snapshot_dir,
            "taxonomy_content_sha256": self.taxonomy_content_sha256,
            "snapshot_file_sha256": self.snapshot_file_sha256,
            "manifest_sha256": self.manifest_sha256,
            "readme_sha256": self.readme_sha256,
            "skill_count": self.skill_count,
            "active_skill_count": self.active_skill_count,
            "deprecated_skill_count": self.deprecated_skill_count,
            "alias_count": self.alias_count,
            "registry_count": self.registry_count,
            "excluded_invalid_artifacts": list(self.excluded_invalid_artifacts),
            "idempotent": self.idempotent,
            "source_commit": self.source_commit,
            "source_branch": self.source_branch,
        }


class TaxonomySnapshotService:
    """Build, verify, and publish a deterministic taxonomy snapshot."""

    def __init__(
        self,
        *,
        source_product: str,
        source_repository: str,
        source_branch: str,
        source_commit_resolver=None,
    ) -> None:
        self.source_product = source_product
        self.source_repository = source_repository
        self.source_branch = source_branch
        self._source_commit_resolver = source_commit_resolver or _default_source_commit_resolver

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def export(
        self,
        output_root: Path,
        *,
        git_commit: Optional[str] = None,
    ) -> TaxonomySnapshotResult:
        """Export a snapshot under ``output_root``.

        Parameters
        ----------
        output_root:
            Existing directory that will receive the versioned snapshot
            subdirectory. The exporter never creates the root itself.
        git_commit:
            Optional override for the source commit. Tests use this to
            inject deterministic metadata.
        """
        if not isinstance(output_root, Path):
            output_root = Path(output_root)
        if not output_root.is_dir():
            raise TaxonomySnapshotEnvironmentError(
                f"Output root does not exist or is not a directory: {output_root}"
            )

        source_commit = git_commit or self._source_commit_resolver()
        _validate_source_commit(source_commit)

        # Build everything before any staging write so the source-state
        # validation cannot be bypassed by a partial export.
        skills = self._collect_exportable_skills()

        # First: build the deterministic skills array and hash it to
        # derive the taxonomy_version. The hash is computed over the
        # canonical ``skills`` array bytes, NOT over the full payload.
        skills_array = self._build_skills_array(skills)
        skills_bytes = _serialize_json_deterministically(skills_array)
        taxonomy_content_sha = hashlib.sha256(skills_bytes).hexdigest()
        taxonomy_version = f"sha256:{taxonomy_content_sha}"

        # Second: build the full taxonomy payload including the version
        # and recompute its bytes. The payload is what gets written to
        # disk, so its file digest is the manifest ``snapshot_sha256``.
        taxonomy = self._build_taxonomy_payload(
            skills=skills,
            skills_array=skills_array,
            taxonomy_version=taxonomy_version,
        )
        taxonomy_bytes = _serialize_json_deterministically(taxonomy)
        snapshot_file_sha = hashlib.sha256(taxonomy_bytes).hexdigest()

        manifest = self._build_manifest_payload(
            taxonomy=taxonomy,
            taxonomy_version=taxonomy_version,
            taxonomy_content_sha256=taxonomy_content_sha,
            snapshot_file_sha256=snapshot_file_sha,
            source_commit=source_commit,
        )
        manifest_bytes = _serialize_json_deterministically(manifest)
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()

        readme_text = self._build_readme()
        readme_bytes = readme_text.encode("utf-8")
        readme_sha = hashlib.sha256(readme_bytes).hexdigest()

        checksums = self._build_checksums(
            {
                SNAPSHOT_FILENAME: taxonomy_bytes,
                MANIFEST_FILENAME: manifest_bytes,
                README_FILENAME: readme_bytes,
            }
        )

        version_dir_name = _safe_version_dir_name(taxonomy_version)
        target_dir = output_root / version_dir_name

        idempotent = self._publish_atomically(
            output_root=output_root,
            target_dir=target_dir,
            files={
                SNAPSHOT_FILENAME: taxonomy_bytes,
                MANIFEST_FILENAME: manifest_bytes,
                README_FILENAME: readme_bytes,
                SHASUMS_FILENAME: checksums.encode("utf-8"),
            },
        )

        return TaxonomySnapshotResult(
            taxonomy_version=taxonomy_version,
            snapshot_dir=str(target_dir),
            taxonomy_content_sha256=taxonomy_content_sha,
            snapshot_file_sha256=snapshot_file_sha,
            manifest_sha256=manifest_sha,
            readme_sha256=readme_sha,
            skill_count=taxonomy["skill_count"],
            active_skill_count=taxonomy["active_skill_count"],
            deprecated_skill_count=taxonomy["deprecated_skill_count"],
            alias_count=manifest["alias_count"],
            registry_count=manifest["registry_count"],
            excluded_invalid_artifacts=EXCLUDED_INVALID_ARTIFACTS,
            idempotent=idempotent,
            source_commit=source_commit,
            source_branch=self.source_branch,
        )

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def _collect_exportable_skills(self) -> List[Skill]:
        # 1) Verify every registry canonical row exists in the database
        #    with the right UUID. Fail closed before any other work.
        registry_entries = list(skill_uid_registry.registry_entries())
        registry_names = {name for name, _ in registry_entries}
        registry_uuids = {uuid.UUID(uid) for _, uid in registry_entries}

        for canonical, uid in registry_entries:
            if not Skill.objects.filter(canonical_name=canonical).exists():
                raise TaxonomySnapshotContractError(
                    f"Registry canonical row missing: {canonical!r}"
                )

        deprecated_dotnet_core_uuid = self._registry_uuid_for(
            DOTNET_CANONICAL_NAME, required=True
        )

        # The deprecated `.NET Core` row is the *only* additional row we
        # export that is not part of the current canonical registry. It
        # must exist in the database, be unique, and must carry a UUIDv4
        # that does not collide with the canonical `.NET` registry UUID.
        deprecated_dotnet_core_qs = Skill.objects.filter(
            canonical_name=DEPRECATED_DOTNET_CORE_CANONICAL_NAME
        )
        deprecated_count = deprecated_dotnet_core_qs.count()
        if deprecated_count > 1:
            raise TaxonomySnapshotContractError(
                f"Multiple `.NET Core` rows detected: {deprecated_count}."
            )
        if deprecated_count == 0:
            raise TaxonomySnapshotContractError(
                "Deprecated `.NET Core` row missing."
            )
        deprecated_dotnet_core = deprecated_dotnet_core_qs.get()
        if deprecated_dotnet_core.is_active:
            raise TaxonomySnapshotContractError(
                "Deprecated `.NET Core` row must be inactive."
            )
        if deprecated_dotnet_core.skill_uid is None:
            raise TaxonomySnapshotContractError(
                "Deprecated `.NET Core` row has no skill_uid."
            )
        deprecated_dotnet_core_uid = deprecated_dotnet_core.skill_uid
        if deprecated_dotnet_core_uid.version != 4:
            raise TaxonomySnapshotContractError(
                f"Deprecated `.NET Core` skill_uid is not UUIDv4: "
                f"{deprecated_dotnet_core_uid}"
            )
        if deprecated_dotnet_core_uid == deprecated_dotnet_core_uuid:
            raise TaxonomySnapshotContractError(
                "Deprecated `.NET Core` skill_uid collides with the "
                "canonical `.NET` registry UUID."
            )
        if deprecated_dotnet_core_uid in registry_uuids:
            raise TaxonomySnapshotContractError(
                "Deprecated `.NET Core` skill_uid collides with a "
                "registry UUID."
            )

        # 2) Verify the invalid artifact state when it is present in
        #    the database. The exporter never mutates taxonomy data,
        #    so the row may already be cleaned up; if it remains, its
        #    state must match the contract exactly.
        invalid_qs = Skill.objects.filter(
            canonical_name=INVALID_ARTIFACT_CANONICAL_NAME
        )
        invalid_count = invalid_qs.count()
        if invalid_count > 1:
            raise TaxonomySnapshotContractError(
                f"Invalid artifact row appears {invalid_count} times; expected at most one."
            )
        if invalid_count == 1:
            invalid_row = invalid_qs.get()
            if invalid_row.is_active:
                raise TaxonomySnapshotContractError(
                    f"Invalid artifact row {INVALID_ARTIFACT_CANONICAL_NAME!r} "
                    "is active; expected inactive."
                )
            if invalid_row.skill_uid != INVALID_ARTIFACT_TOMBSTONE_UUID:
                raise TaxonomySnapshotContractError(
                    f"Invalid artifact row tombstone mismatch: expected "
                    f"{INVALID_ARTIFACT_TOMBSTONE_UUID} got {invalid_row.skill_uid}."
                )

        # 3) Refuse any unknown non-registry, non-deprecated,
        #    non-invalid-artifact row. This is the strict "no foreign
        #    identity" guard.
        allowed_non_registry_uuids = {
            deprecated_dotnet_core_uid,
            *(uuid.UUID(uid) for _, uid in registry_entries),
        }
        if invalid_count == 1:
            allowed_non_registry_uuids.add(INVALID_ARTIFACT_TOMBSTONE_UUID)
        unknown_rows = (
            Skill.objects.exclude(skill_uid__in=allowed_non_registry_uuids)
        )
        unknown_names = sorted(
            unknown_rows.values_list("canonical_name", flat=True)
        )
        if unknown_names:
            raise TaxonomySnapshotContractError(
                "Unknown non-registry Skill rows detected: "
                + ", ".join(repr(n) for n in unknown_names)
            )

        selected: List[Skill] = []
        seen_uuids: set = set()
        seen_names: set = set()
        seen_slugs: set = set()

        # 4) All current canonical registry skills, in registry name
        #    order. The slug uniqueness check below is run after
        #    fallback derivation so that a real database collision on
        #    the derived slug is still caught.
        for skill in (
            Skill.objects.filter(canonical_name__in=sorted(registry_names))
            .order_by("canonical_name")
        ):
            self._check_skill_for_export(
                skill,
                registry_names=registry_names,
                seen_uuids=seen_uuids,
                seen_names=seen_names,
                seen_slugs=seen_slugs,
            )
            selected.append(skill)

        # 5) Deprecated legacy rows (only `.NET Core` for this gate).
        self._check_skill_for_export(
            deprecated_dotnet_core,
            registry_names=registry_names,
            seen_uuids=seen_uuids,
            seen_names=seen_names,
            seen_slugs=seen_slugs,
            allow_non_registry=True,
        )
        selected.append(deprecated_dotnet_core)

        # 6) Validate the post-fallback slug uniqueness using the
        #    exact same derivation logic the payload uses. A real
        #    collision after fallback would otherwise be invisible to
        #    a raw-database uniqueness check.
        derived_slugs: List[str] = []
        for skill in selected:
            slug = skill.slug or _derive_slug_fallback(skill.canonical_name)
            derived_slugs.append(slug)
        if len(set(derived_slugs)) != len(derived_slugs):
            seen: set = set()
            duplicates = sorted(
                s for s in derived_slugs if s in seen or seen.add(s)
            )
            raise TaxonomySnapshotContractError(
                "Duplicate derived slugs after fallback: "
                + ", ".join(repr(s) for s in duplicates)
            )

        # 7) Sort by skill_uid string for determinism.
        selected.sort(key=lambda s: str(s.skill_uid))
        if len(selected) != EXPECTED_TOTAL_SKILL_COUNT:
            raise TaxonomySnapshotContractError(
                f"Snapshot skill count mismatch: expected "
                f"{EXPECTED_TOTAL_SKILL_COUNT} got {len(selected)}."
            )
        active = sum(1 for s in selected if s.is_active)
        deprecated = sum(1 for s in selected if not s.is_active)
        if active != EXPECTED_ACTIVE_SKILL_COUNT:
            raise TaxonomySnapshotContractError(
                f"Active skill count mismatch: expected "
                f"{EXPECTED_ACTIVE_SKILL_COUNT} got {active}."
            )
        if deprecated != EXPECTED_DEPRECATED_SKILL_COUNT:
            raise TaxonomySnapshotContractError(
                f"Deprecated skill count mismatch: expected "
                f"{EXPECTED_DEPRECATED_SKILL_COUNT} got {deprecated}."
            )
        return selected

    def _check_skill_for_export(
        self,
        skill: Skill,
        *,
        registry_names: set,
        seen_uuids: set,
        seen_names: set,
        seen_slugs: set,
        allow_non_registry: bool = False,
    ) -> None:
        if skill.skill_uid is None:
            raise TaxonomySnapshotContractError(
                f"Skill row {skill.canonical_name!r} is missing skill_uid."
            )
        if skill.skill_uid.version != 4:
            raise TaxonomySnapshotContractError(
                f"Skill row {skill.canonical_name!r} has non-UUIDv4 skill_uid: "
                f"{skill.skill_uid}"
            )
        in_registry = skill.canonical_name in registry_names
        if not in_registry and not allow_non_registry:
            raise TaxonomySnapshotContractError(
                f"Skill row {skill.canonical_name!r} is not in the canonical "
                "registry and is not an approved deprecated row."
            )
        if in_registry:
            expected = skill_uid_registry.get_skill_uid(skill.canonical_name)
            if skill.skill_uid != expected:
                raise TaxonomySnapshotContractError(
                    f"Skill row {skill.canonical_name!r} has skill_uid "
                    f"{skill.skill_uid} but the registry requires {expected}."
                )
        if skill.skill_uid in seen_uuids:
            raise TaxonomySnapshotContractError(
                f"Duplicate skill_uid encountered: {skill.skill_uid}"
            )
        if skill.canonical_name in seen_names:
            raise TaxonomySnapshotContractError(
                f"Duplicate canonical_name encountered: {skill.canonical_name!r}"
            )
        slug = skill.slug or _derive_slug_fallback(skill.canonical_name)
        if slug in seen_slugs:
            raise TaxonomySnapshotContractError(
                f"Duplicate derived slug encountered: {slug!r}"
            )
        seen_uuids.add(skill.skill_uid)
        seen_names.add(skill.canonical_name)
        seen_slugs.add(slug)

    @staticmethod
    def _registry_uuid_for(canonical_name: str, *, required: bool) -> uuid.UUID:
        if not skill_uid_registry.has_skill_uid(canonical_name):
            if required:
                raise TaxonomySnapshotContractError(
                    f"Canonical skill {canonical_name!r} is missing from the registry."
                )
            raise TaxonomySnapshotContractError(
                f"Canonical skill {canonical_name!r} is missing from the registry."
            )
        return skill_uid_registry.get_skill_uid(canonical_name)

    # ------------------------------------------------------------------
    # Payload assembly
    # ------------------------------------------------------------------

    def _build_taxonomy_payload(
        self,
        *,
        skills: List[Skill],
        skills_array: List[dict],
        taxonomy_version: str,
    ) -> dict:
        active_count = sum(1 for s in skills if s.is_active)
        deprecated_count = sum(1 for s in skills if not s.is_active)

        return {
            "format_name": SNAPSHOT_FORMAT_NAME,
            "format_version": SNAPSHOT_FORMAT_VERSION,
            "taxonomy_version": taxonomy_version,
            "skill_count": len(skills_array),
            "active_skill_count": active_count,
            "deprecated_skill_count": deprecated_count,
            "skills": skills_array,
        }

    def _build_skills_array(self, skills: List[Skill]) -> List[dict]:
        return [self._build_skill_entry(skill) for skill in skills]

    def _build_skill_entry(self, skill: Skill) -> dict:
        if skill.skill_uid is None:
            raise TaxonomySnapshotContractError(
                f"Skill {skill.canonical_name!r} has no skill_uid."
            )
        if skill.skill_uid.version != 4:
            raise TaxonomySnapshotContractError(
                f"Skill {skill.canonical_name!r} has non-UUIDv4 skill_uid."
            )
        # The Django ``.NET`` row pre-exists the snapshot contract and
        # carries an empty ``slug``; the contract requires a non-empty
        # string. The exporter never rewrites the database, so it derives
        # a deterministic fallback from the canonical name. The
        # canonical name, aliases, categories, UUIDs, and source field
        # remain the database values.
        slug = skill.slug
        if not slug:
            slug = _derive_slug_fallback(skill.canonical_name)
        entry = {
            "skill_uid": str(skill.skill_uid),
            "canonical_name": skill.canonical_name,
            "slug": slug,
            "category": skill.category,
            "is_active": bool(skill.is_active),
            "source": skill.source,
            "esco_uri": skill.esco_uri,
            "aliases": self._collect_alias_entries(skill),
        }
        if not skill.is_active:
            entry["deprecation"] = self._build_deprecation_block(skill)
        else:
            entry["deprecation"] = None
        return entry

    @staticmethod
    def _collect_alias_entries(skill: Skill) -> List[dict]:
        aliases = list(
            SkillAlias.objects.filter(skill=skill).order_by(
                "normalized_alias", "language", "alias"
            )
        )
        seen_norm: set = set()
        seen_inside: set = set()
        entries: List[dict] = []
        for alias in aliases:
            if alias.normalized_alias in seen_norm:
                raise TaxonomySnapshotContractError(
                    f"Duplicate normalized alias {alias.normalized_alias!r} "
                    f"on skill {skill.canonical_name!r}."
                )
            if alias.normalized_alias in seen_inside:
                # Defensive guard: the database constraint already
                # prevents the same skill from carrying two aliases
                # with the same normalized form, but a future
                # refactor or fixture could regress. The exporter
                # fails closed in that case.
                raise TaxonomySnapshotContractError(
                    f"Duplicate normalized alias {alias.normalized_alias!r} "
                    f"on skill {skill.canonical_name!r}."
                )
            seen_norm.add(alias.normalized_alias)
            seen_inside.add(alias.normalized_alias)
            entries.append(
                {
                    "alias": alias.alias,
                    "normalized_alias": alias.normalized_alias,
                    "language": alias.language,
                }
            )
        return entries

    def _build_deprecation_block(self, skill: Skill) -> dict:
        if skill.canonical_name == DEPRECATED_DOTNET_CORE_CANONICAL_NAME:
            replacement = skill_uid_registry.require_skill_uid(DOTNET_CANONICAL_NAME)
            return {
                "status": "deprecated",
                "reason": "canonical_rename",
                "replacement_skill_uid": str(replacement),
            }
        raise TaxonomySnapshotContractError(
            f"Skill {skill.canonical_name!r} is inactive but has no approved "
            "deprecation metadata for this gate."
        )

    def _build_manifest_payload(
        self,
        *,
        taxonomy: dict,
        taxonomy_version: str,
        taxonomy_content_sha256: str,
        snapshot_file_sha256: str,
        source_commit: str,
    ) -> dict:
        alias_count = sum(
            len(entry["aliases"]) for entry in taxonomy["skills"]
        )
        return {
            "manifest_format": "tuniatlas_taxonomy_snapshot_manifest",
            "manifest_version": 1,
            "taxonomy_version": taxonomy_version,
            "taxonomy_content_sha256": taxonomy_content_sha256,
            "snapshot_filename": SNAPSHOT_FILENAME,
            "snapshot_sha256": snapshot_file_sha256,
            "source_product": self.source_product,
            "source_repository": self.source_repository,
            "source_branch": self.source_branch,
            "source_commit": source_commit,
            "source_skills_migration": REQUIRED_SOURCE_MIGRATION,
            "registry_count": skill_uid_registry.registry_count(),
            "snapshot_skill_count": taxonomy["skill_count"],
            "active_skill_count": taxonomy["active_skill_count"],
            "deprecated_skill_count": taxonomy["deprecated_skill_count"],
            "alias_count": alias_count,
            "excluded_invalid_artifacts": list(EXCLUDED_INVALID_ARTIFACTS),
            "exporter_contract_version": EXPORTER_CONTRACT_VERSION,
        }

    @staticmethod
    def _build_readme() -> str:
        return (
            "TuniAtlas Jobs skill taxonomy snapshot\n"
            "=====================================\n"
            "\n"
            "- Generated by the TuniAtlas Jobs Django canonical taxonomy exporter.\n"
            "- Consumed by the private `tuniatlas-ml` workspace.\n"
            "- Contains no user, CV, job, profile, email, telephone, address, or\n"
            "  credential data.\n"
            "- `skill_uid` is the immutable cross-environment identity for every\n"
            "  canonical and deprecated skill in this snapshot.\n"
            "- Internal Django integer IDs are intentionally excluded.\n"
            "- The formal JSON Schema for taxonomy snapshots is deferred to ML-1.\n"
            "- This artifact must remain under private ignored data storage and\n"
            "  later encrypted backup.\n"
        )

    @staticmethod
    def _build_checksums(files: Dict[str, bytes]) -> str:
        rows: List[str] = []
        for name in sorted(files):
            digest = hashlib.sha256(files[name]).hexdigest()
            rows.append(f"{digest}  {name}")
        return "\n".join(rows) + "\n"

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------

    def _publish_atomically(
        self,
        *,
        output_root: Path,
        target_dir: Path,
        files: Dict[str, bytes],
    ) -> bool:
        """Atomically publish ``files`` to ``target_dir``.

        The staging directory is created under ``output_root`` so the
        final ``rename`` is on the same filesystem. Every file is
        written and verified inside staging only; the final target is
        produced by a single atomic rename. If the target already
        exists, it is read back and verified: a complete identical
        directory is treated as idempotent success, anything else fails
        closed. Returns ``True`` when an existing identical snapshot
        was reused, ``False`` when a new snapshot was published.
        """
        staging_dir: Optional[Path] = None
        try:
            staging_dir = Path(
                tempfile.mkdtemp(prefix=STAGING_DIR_PREFIX, dir=str(output_root))
            )
        except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
            raise TaxonomySnapshotPublishError(
                f"Could not create staging directory under {output_root}: {exc}"
            ) from exc

        try:
            self._write_staging(staging_dir, files)
            self._verify_staging(staging_dir, files)
            if target_dir.exists():
                existing = self._read_complete_target(target_dir)
                if existing is None:
                    self._cleanup_staging(staging_dir)
                    raise TaxonomySnapshotPublishError(
                        f"Refusing to overwrite incomplete target: {target_dir}"
                    )
                if existing != files:
                    self._cleanup_staging(staging_dir)
                    raise TaxonomySnapshotPublishError(
                        f"Refusing to overwrite differing snapshot: {target_dir}"
                    )
                self._cleanup_staging(staging_dir)
                return True
            try:
                os.replace(str(staging_dir), str(target_dir))
            except OSError as exc:
                self._cleanup_staging(staging_dir)
                # If the target appeared during the rename, fail closed
                # rather than overwriting or leaving a partial state.
                if target_dir.exists():
                    raise TaxonomySnapshotPublishError(
                        f"Refusing to overwrite snapshot that appeared during publish: "
                        f"{target_dir}"
                    ) from exc
                raise TaxonomySnapshotPublishError(
                    f"Atomic rename of staging to {target_dir} failed: {exc}"
                ) from exc
            return False
        except BaseException:
            self._cleanup_staging(staging_dir)
            raise

    @staticmethod
    def _write_staging(staging_dir: Path, files: Dict[str, bytes]) -> None:
        for name, data in files.items():
            path = staging_dir / name
            with open(path, "wb") as fp:
                fp.write(data)
                fp.flush()
                try:
                    os.fsync(fp.fileno())
                except OSError:
                    # fsync is best-effort; some filesystems do not
                    # support it. Continue without failing the export.
                    pass
        try:
            dir_fd = os.open(str(staging_dir), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass

    @staticmethod
    def _verify_staging(staging_dir: Path, files: Dict[str, bytes]) -> None:
        for name, data in files.items():
            path = staging_dir / name
            if not path.is_file():
                raise TaxonomySnapshotPublishError(
                    f"Staging file missing after write: {name}"
                )
            actual = path.read_bytes()
            if actual != data:
                raise TaxonomySnapshotPublishError(
                    f"Staging verification failed for {name}: written bytes differ."
                )

    @staticmethod
    def _read_complete_target(target_dir: Path) -> Optional[Dict[str, bytes]]:
        if not target_dir.is_dir():
            return None
        existing: Dict[str, bytes] = {}
        required = (
            SNAPSHOT_FILENAME,
            MANIFEST_FILENAME,
            README_FILENAME,
            SHASUMS_FILENAME,
        )
        for name in required:
            path = target_dir / name
            if not path.is_file():
                return None
            existing[name] = path.read_bytes()
        # Refuse to silently reuse a directory that also carries extra
        # regular files or subdirectories.
        for child in target_dir.iterdir():
            if child.name not in required:
                return None
        return existing

    @staticmethod
    def _cleanup_staging(staging_dir: Optional[Path]) -> None:
        if staging_dir is None:
            return
        shutil.rmtree(staging_dir, ignore_errors=True)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _serialize_json_deterministically(payload: dict) -> bytes:
    """Serialize ``payload`` deterministically.

    The result is byte-for-byte identical for an unchanged input.
    """
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        separators=(",", ": "),
    ).encode("utf-8") + b"\n"


def _derive_slug_fallback(canonical_name: str) -> str:
    """Derive a non-empty slug fallback from a canonical name.

    Used only when the database carries an empty ``slug``. The
    algorithm is intentionally simple and deterministic.
    """
    if not canonical_name:
        raise TaxonomySnapshotContractError(
            "Cannot derive slug fallback: canonical_name is empty."
        )
    lowered = canonical_name.lower()
    out: List[str] = []
    for char in lowered:
        if char.isalnum():
            out.append(char)
        elif char in {" ", "-", "_", ".", "/"}:
            out.append("-")
    slug = "".join(out)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        # Last-resort fallback for canonical names that contain
        # nothing alphanumeric. This is unreachable in the ML-0 gate
        # because the registry is curated, but kept defensive.
        slug = "skill"
    return slug


def _safe_version_dir_name(taxonomy_version: str) -> str:
    if not taxonomy_version.startswith("sha256:"):
        raise TaxonomySnapshotContractError(
            f"Unsupported taxonomy version format: {taxonomy_version!r}"
        )
    digest = taxonomy_version[len("sha256:"):]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise TaxonomySnapshotContractError(
            f"Invalid taxonomy version digest: {taxonomy_version!r}"
        )
    return f"sha256-{digest}"


def _validate_source_commit(source_commit: str) -> None:
    if not isinstance(source_commit, str) or not SOURCE_COMMIT_RE.fullmatch(source_commit):
        raise TaxonomySnapshotContractError(
            f"Source commit must be a 40-character lowercase hex SHA-1: "
            f"{source_commit!r}"
        )


def _default_source_commit_resolver() -> str:
    """Resolve the current Django source commit safely.

    The exporter runs in the Django repository worktree. The command
    refuses to run on a dirty worktree, so the resolved commit is the
    authoritative commit of the export.
    """
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise TaxonomySnapshotEnvironmentError(
            f"Could not resolve source commit: {exc}"
        ) from exc
    return completed.stdout.strip()


def assert_source_environment(*, require_branch: Optional[str] = None) -> None:
    """Verify migrations and clean worktree at the exporter boundary.

    Tests inject ``require_branch=None`` to disable the branch check.
    """
    from django.core.management import call_command
    from io import StringIO

    out = StringIO()
    try:
        call_command("showmigrations", REQUIRED_SOURCE_MIGRATION_APP, stdout=out)
    except Exception as exc:  # pragma: no cover - delegated
        raise TaxonomySnapshotEnvironmentError(
            f"Could not inspect migrations: {exc}"
        ) from exc
    text = out.getvalue()
    # Each applied migration line looks like ``[X] 0004_skill_skill_uid_finalize``.
    for migration in ("0001_initial", REQUIRED_SOURCE_MIGRATION[len("skills."):]):
        marker = f"[X] {migration}"
        if marker not in text:
            raise TaxonomySnapshotEnvironmentError(
                f"Required migration not applied: {migration}"
            )

    # Git state checks.
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise TaxonomySnapshotEnvironmentError(
            f"Could not read git status: {exc}"
        ) from exc
    if status.stdout.strip():
        raise TaxonomySnapshotEnvironmentError(
            "Refusing to export from a dirty worktree."
        )
    if require_branch is not None:
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise TaxonomySnapshotEnvironmentError(
                f"Could not read current branch: {exc}"
            ) from exc
        actual_branch = branch.stdout.strip()
        if actual_branch != require_branch:
            raise TaxonomySnapshotEnvironmentError(
                f"Refusing to export from branch {actual_branch!r}; "
                f"expected {require_branch!r}."
            )


def verify_snapshot_against_database(snapshot_dir: Path) -> None:
    """Cross-check an existing snapshot against the live database.

    Used by tests to prove the live database is unchanged after an
    export. Raises if the snapshot cannot be matched.
    """
    snapshot_path = snapshot_dir / SNAPSHOT_FILENAME
    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    service = TaxonomySnapshotService(
        source_product="verify",
        source_repository="verify",
        source_branch="verify",
    )
    expected_skills = service._collect_exportable_skills()
    expected_skills_array = service._build_skills_array(expected_skills)
    expected_skills_bytes = _serialize_json_deterministically(expected_skills_array)
    expected_taxonomy_sha = hashlib.sha256(expected_skills_bytes).hexdigest()
    expected_taxonomy_version = f"sha256:{expected_taxonomy_sha}"
    expected = service._build_taxonomy_payload(
        skills=expected_skills,
        skills_array=expected_skills_array,
        taxonomy_version=expected_taxonomy_version,
    )
    expected_bytes = _serialize_json_deterministically(expected)
    if expected != data:
        raise TaxonomySnapshotContractError(
            "Snapshot does not match the current database state."
        )
    if expected_bytes != snapshot_path.read_bytes():
        raise TaxonomySnapshotContractError(
            "Snapshot bytes are not byte-identical to the canonical serialization."
        )
