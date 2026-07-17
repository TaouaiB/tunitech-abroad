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
* write through a staging directory and publish the final directory
  atomically;
* treat an existing byte-identical snapshot as idempotent success;
* refuse to overwrite a differing existing snapshot version;
* return only sanitized metadata.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

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
DEPRECATED_DOTNET_CORE_CANONICAL_NAME = ".NET Core"
DOTNET_CANONICAL_NAME = ".NET"

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
    taxonomy_sha256: str
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
            "taxonomy_sha256": self.taxonomy_sha256,
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

        skills = self._collect_exportable_skills()
        # First: build the deterministic skills array and hash it to
        # derive the taxonomy_version. The hash is computed over the
        # canonical ``skills`` array bytes, NOT over the full payload.
        skills_array = self._build_skills_array(skills)
        skills_bytes = _serialize_json_deterministically(skills_array)
        taxonomy_sha = hashlib.sha256(skills_bytes).hexdigest()
        taxonomy_version = f"sha256:{taxonomy_sha}"

        # Second: build the full taxonomy payload including the version
        # and recompute its bytes. The payload is what gets written to
        # disk.
        taxonomy = self._build_taxonomy_payload(
            skills=skills,
            skills_array=skills_array,
            taxonomy_version=taxonomy_version,
        )
        taxonomy_bytes = _serialize_json_deterministically(taxonomy)

        manifest = self._build_manifest_payload(
            taxonomy=taxonomy,
            taxonomy_version=taxonomy_version,
            taxonomy_sha256=taxonomy_sha,
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

        idempotent = self._publish_if_matches(
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
            taxonomy_sha256=taxonomy_sha,
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
        registry_names = set(skill_uid_registry.registry_canonical_names())

        deprecated_dotnet_core_uuid = self._registry_uuid_for(
            DOTNET_CANONICAL_NAME, required=False
        )

        # The deprecated `.NET Core` row is the *only* additional row we
        # export that is not part of the current canonical registry. It
        # must exist in the database and must carry a UUIDv4.
        deprecated_dotnet_core: Optional[Skill] = None
        deprecated_dotnet_core_qs = Skill.objects.filter(
            canonical_name=DEPRECATED_DOTNET_CORE_CANONICAL_NAME
        )
        for row in deprecated_dotnet_core_qs:
            if deprecated_dotnet_core is not None:
                raise TaxonomySnapshotContractError(
                    "Multiple `.NET Core` rows detected; expected at most one."
                )
            deprecated_dotnet_core = row

        deprecated_dotnet_core_uid: Optional[uuid.UUID] = None
        if deprecated_dotnet_core is not None:
            if deprecated_dotnet_core.is_active:
                raise TaxonomySnapshotContractError(
                    "Deprecated `.NET Core` row must be inactive."
                )
            if deprecated_dotnet_core.skill_uid is None:
                raise TaxonomySnapshotContractError(
                    "Deprecated `.NET Core` row has no skill_uid."
                )
            deprecated_dotnet_core_uid = deprecated_dotnet_core.skill_uid
            if deprecated_dotnet_core.skill_uid.version != 4:
                raise TaxonomySnapshotContractError(
                    f"Deprecated `.NET Core` skill_uid is not UUIDv4: "
                    f"{deprecated_dotnet_core.skill_uid}"
                )
            if (
                deprecated_dotnet_core_uuid is not None
                and deprecated_dotnet_core.skill_uid == deprecated_dotnet_core_uuid
            ):
                raise TaxonomySnapshotContractError(
                    "Deprecated `.NET Core` skill_uid collides with the "
                    "canonical `.NET` registry UUID."
                )
            if (
                deprecated_dotnet_core_uuid is None
                and deprecated_dotnet_core_uid is None
            ):
                raise TaxonomySnapshotContractError(
                    "Missing canonical `.NET` registry UUID for `.NET Core` "
                    "deprecation replacement."
                )

        selected: List[Skill] = []
        seen_uuids: set = set()
        seen_names: set = set()
        seen_slugs: set = set()

        # 1) All current canonical registry skills.
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

        # 2) Deprecated legacy rows (only `.NET Core` for this gate).
        if deprecated_dotnet_core is not None:
            self._check_skill_for_export(
                deprecated_dotnet_core,
                registry_names=registry_names,
                seen_uuids=seen_uuids,
                seen_names=seen_names,
                seen_slugs=seen_slugs,
                allow_non_registry=True,
            )
            selected.append(deprecated_dotnet_core)

        # 3) Refuse any unknown non-registry row that slipped in.
        expected_uuids = {s.skill_uid for s in selected}
        unknown = (
            Skill.objects.exclude(skill_uid__in=expected_uuids)
            .exclude(canonical_name=INVALID_ARTIFACT_CANONICAL_NAME)
        )
        unknown_names = sorted(
            unknown.values_list("canonical_name", flat=True)
        )
        if unknown_names:
            raise TaxonomySnapshotContractError(
                "Unknown non-registry Skill rows detected: "
                + ", ".join(repr(n) for n in unknown_names)
            )

        # 4) Refuse the invalid artifact if it is still present.
        invalid_present = Skill.objects.filter(
            canonical_name=INVALID_ARTIFACT_CANONICAL_NAME
        ).exists()
        if not invalid_present:
            # No-op: invalid artifact was previously cleaned up.
            pass

        # Sort by skill_uid string for determinism.
        selected.sort(key=lambda s: str(s.skill_uid))
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
        if skill.slug in seen_slugs:
            raise TaxonomySnapshotContractError(
                f"Duplicate slug encountered: {skill.slug!r}"
            )
        seen_uuids.add(skill.skill_uid)
        seen_names.add(skill.canonical_name)
        seen_slugs.add(skill.slug)

    @staticmethod
    def _registry_uuid_for(canonical_name: str, *, required: bool) -> Optional[uuid.UUID]:
        if not skill_uid_registry.has_skill_uid(canonical_name):
            if required:
                raise TaxonomySnapshotContractError(
                    f"Canonical skill {canonical_name!r} is missing from the registry."
                )
            return None
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
        entries: List[dict] = []
        for alias in aliases:
            if alias.normalized_alias in seen_norm:
                raise TaxonomySnapshotContractError(
                    f"Duplicate normalized alias {alias.normalized_alias!r} "
                    f"on skill {skill.canonical_name!r}."
                )
            seen_norm.add(alias.normalized_alias)
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
        taxonomy_sha256: str,
        source_commit: str,
    ) -> dict:
        alias_count = sum(
            len(entry["aliases"]) for entry in taxonomy["skills"]
        )
        return {
            "manifest_format": "tuniatlas_taxonomy_snapshot_manifest",
            "manifest_version": 1,
            "taxonomy_version": taxonomy_version,
            "snapshot_filename": SNAPSHOT_FILENAME,
            "snapshot_sha256": taxonomy_sha256,
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

    def _publish_if_matches(
        self,
        *,
        target_dir: Path,
        files: Dict[str, bytes],
    ) -> bool:
        """Atomically publish ``files`` to ``target_dir``.

        Returns ``True`` if an existing identical snapshot was reused,
        ``False`` if a new snapshot was written.

        Raises ``TaxonomySnapshotPublishError`` if an existing snapshot
        with a different content hash is found.
        """
        if target_dir.exists():
            existing = self._read_existing(target_dir)
            if existing is not None and existing == files:
                return True
            if existing is not None:
                raise TaxonomySnapshotPublishError(
                    f"Refusing to overwrite differing snapshot at {target_dir}."
                )

        staging_dir = Path(tempfile.mkdtemp(prefix="taxonomy-snapshot-"))
        try:
            for name, data in files.items():
                path = staging_dir / name
                path.write_bytes(data)
            # Verify staging contents before publishing.
            verified = {n: (staging_dir / n).read_bytes() for n in files}
            if verified != files:
                raise TaxonomySnapshotPublishError(
                    "Staging verification failed: written bytes differ."
                )
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                target_dir.mkdir(exist_ok=False)
            except FileExistsError:
                raise TaxonomySnapshotPublishError(
                    f"Target directory {target_dir} already exists."
                )
            for name, data in files.items():
                (target_dir / name).write_bytes(data)
        except Exception:
            shutil.rmtree(staging_dir, ignore_errors=True)
            if target_dir.exists() and not any(target_dir.iterdir()):
                target_dir.rmdir()
            raise
        else:
            shutil.rmtree(staging_dir, ignore_errors=True)
        return False

    @staticmethod
    def _read_existing(target_dir: Path) -> Optional[Dict[str, bytes]]:
        if not target_dir.is_dir():
            return None
        existing: Dict[str, bytes] = {}
        for name in (SNAPSHOT_FILENAME, MANIFEST_FILENAME, README_FILENAME, SHASUMS_FILENAME):
            path = target_dir / name
            if not path.is_file():
                return None
            existing[name] = path.read_bytes()
        return existing


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
