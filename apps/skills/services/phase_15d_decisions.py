import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings


APPROVED_DECISION_FILE = (
    Path(settings.BASE_DIR)
    / "docs"
    / "phases"
    / "phase_15d_curated_taxonomy_and_zero_skill_recovery"
    / "taxonomy_review_decisions_phase_15d_approved.csv"
)


@dataclass(frozen=True)
class Phase15DDecision:
    raw_skill_text: str
    normalized_text: str
    decision: str
    target_canonical_skill: str
    target_category: str


@lru_cache(maxsize=1)
def load_phase_15d_decisions() -> tuple[Phase15DDecision, ...]:
    if not APPROVED_DECISION_FILE.exists():
        return ()

    decisions: list[Phase15DDecision] = []
    with APPROVED_DECISION_FILE.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("approved_for_phase_15d") != "yes":
                continue
            decisions.append(
                Phase15DDecision(
                    raw_skill_text=(row.get("raw_skill_text") or "").strip(),
                    normalized_text=(row.get("normalized_text") or "").strip(),
                    decision=(row.get("proposed_decision") or "").strip(),
                    target_canonical_skill=(row.get("proposed_target_canonical_skill") or "").strip(),
                    target_category=(row.get("proposed_target_category") or "").strip(),
                )
            )
    return tuple(decisions)


def approved_ignore_terms() -> frozenset[str]:
    return frozenset(
        decision.normalized_text
        for decision in load_phase_15d_decisions()
        if decision.decision == "ignore" and decision.normalized_text
    )


def approved_taxonomy_decisions() -> tuple[Phase15DDecision, ...]:
    return tuple(
        decision
        for decision in load_phase_15d_decisions()
        if decision.decision in {"alias_to_existing", "create_new_skill"}
        and decision.raw_skill_text
        and decision.target_canonical_skill
    )


def approved_reconcile_decisions() -> dict[str, Phase15DDecision]:
    return {
        decision.normalized_text: decision
        for decision in load_phase_15d_decisions()
        if decision.normalized_text and decision.decision != "keep_pending"
    }
