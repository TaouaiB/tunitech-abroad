"""Skill UUID registry service.

Loads the committed canonical-skill UUIDv4 registry and exposes lookups
used by the seed service, migrations, and tests.

The registry is a single source of truth for cross-environment
identity of canonical skills. New canonical skills must be appended
to ``apps/skills/data/skill_uid_registry_v1.json`` (or its successor)
before they are produced by the seed path.
"""

from __future__ import annotations

import json
import threading
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Tuple


_REGISTRY_FILENAME = "skill_uid_registry_v1.json"
_REGISTRY_VERSION = 1


def _registry_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / _REGISTRY_FILENAME


@lru_cache(maxsize=1)
def _load_registry_cached() -> Tuple[Dict[str, uuid.UUID], Tuple[Tuple[str, str], ...], int]:
    """Load and validate the registry.

    Returns a tuple of:
        - mapping from canonical_name -> UUID
        - ordered tuple of (canonical_name, skill_uid_str) pairs
        - registry version
    """
    path = _registry_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Skill UID registry not found at {path}. "
            "The committed registry is required for cross-environment skill identity."
        )
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Skill UID registry must be a JSON object")
    version = data.get("version")
    if version != _REGISTRY_VERSION:
        raise ValueError(
            f"Unsupported skill UID registry version: {version} (expected {_REGISTRY_VERSION})"
        )
    skills = data.get("skills")
    if not isinstance(skills, list):
        raise ValueError("Skill UID registry 'skills' must be a list")

    name_to_uid: Dict[str, uuid.UUID] = {}
    ordered: list[Tuple[str, str]] = []
    seen_names: set[str] = set()
    seen_uuids: set[uuid.UUID] = set()

    for entry in skills:
        if not isinstance(entry, dict):
            raise ValueError(f"Registry entry must be an object: {entry!r}")
        name = entry.get("canonical_name")
        raw_uid = entry.get("skill_uid")
        if not isinstance(name, str) or not name:
            raise ValueError(f"Registry entry missing canonical_name: {entry!r}")
        if not isinstance(raw_uid, str) or not raw_uid:
            raise ValueError(f"Registry entry missing skill_uid: {entry!r}")
        try:
            uid = uuid.UUID(raw_uid)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid UUID in registry entry: {raw_uid!r}") from exc
        if uid.version != 4:
            raise ValueError(
                f"Registry entry for {name!r} is not UUIDv4: {raw_uid!r} (version={uid.version})"
            )
        if name in seen_names:
            raise ValueError(f"Duplicate canonical_name in registry: {name!r}")
        if uid in seen_uuids:
            raise ValueError(f"Duplicate skill_uid in registry: {raw_uid!r}")
        seen_names.add(name)
        seen_uuids.add(uid)
        name_to_uid[name] = uid
        ordered.append((name, raw_uid))

    return name_to_uid, tuple(ordered), version


def reset_cache() -> None:
    """Clear the cached registry. Used by tests after editing the registry file."""
    _load_registry_cached.cache_clear()


def registry_version() -> int:
    """Return the registry schema version."""
    _load_registry_cached.cache_clear()
    return _load_registry_cached()[2]


def registry_path() -> Path:
    """Return the absolute path of the committed registry file."""
    return _registry_path()


def get_skill_uid(canonical_name: str) -> uuid.UUID:
    """Return the registry UUID for a canonical skill name.

    Raises:
        KeyError: if the canonical name is not present in the registry.
    """
    name_to_uid, _, _ = _load_registry_cached()
    return name_to_uid[canonical_name]


def has_skill_uid(canonical_name: str) -> bool:
    """Return True if the canonical name is in the registry."""
    name_to_uid, _, _ = _load_registry_cached()
    return canonical_name in name_to_uid


def registry_canonical_names() -> Tuple[str, ...]:
    """Return registry canonical names in their committed order."""
    _, ordered, _ = _load_registry_cached()
    return tuple(name for name, _ in ordered)


def registry_entries() -> Tuple[Tuple[str, str], ...]:
    """Return registry entries as ``(canonical_name, skill_uid_str)`` pairs."""
    _, ordered, _ = _load_registry_cached()
    return ordered


def registry_count() -> int:
    """Return the number of canonical skills in the registry."""
    _, ordered, _ = _load_registry_cached()
    return len(ordered)


def assert_registry_complete(seed_canonical_names: Iterable[str]) -> None:
    """Validate that every seed canonical name has a registry entry.

    Raises:
        ValueError: when at least one seed canonical name is missing.
    """
    name_to_uid, _, _ = _load_registry_cached()
    missing = sorted({n for n in seed_canonical_names if n not in name_to_uid})
    if missing:
        raise ValueError(
            "Skill UID registry is missing entries for seed canonical skills: "
            + ", ".join(repr(n) for n in missing)
        )


# Re-export threading.Lock for callers that need to serialize registry mutations
# (the registry is read-only at runtime, but tests may write to the file).
_file_lock = threading.Lock()
