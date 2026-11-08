"""Lossless source-duration preservation without choosing an unstated retention policy."""

import re
from copy import deepcopy

from .schemas import Evidence

BOUND = (
    r"(?:(?:a |the )?(?:minimum|maximum)(?: (?:retention )?(?:period|duration))?"
    r"(?: of)?|at least|at most)"
)


def preserve_retention_duration(requirement: dict, evidence: list[Evidence]) -> tuple[dict, bool]:
    """Remove only added bounds on an exact, unqualified stakeholder retention duration."""
    result = deepcopy(requirement)
    linked = [
        item.quote
        for item in evidence
        if item.id in requirement["evidence_ids"]
        and re.search(r"\b(?:retain\w*|retention|keep)\b", item.quote, re.I)
    ]
    changed = False
    for quote in linked:
        for value, unit in re.findall(r"\b([0-9]+)\s+(days?|hours?|months?|years?)\b", quote, re.I):
            duration = rf"{re.escape(value)}\s+{re.escape(unit)}"
            # A source-specified bound (including a trailing qualifier) is immutable.
            if re.search(rf"{BOUND}\s+{duration}|{duration}\s+(?:minimum|maximum)", quote, re.I):
                continue
            pattern = re.compile(rf"\b{BOUND}\s+({duration})\b", re.I)
            for field in ("statement", "rationale"):
                if field in result:
                    result[field], count = pattern.subn(r"\1", result[field])
                    changed |= bool(count)
            for criterion in result.get("acceptance_criteria", []):
                for field in ("given", "when", "then", "observable_evidence"):
                    criterion[field], count = pattern.subn(r"\1", criterion[field])
                    changed |= bool(count)
    if (
        changed
        and "unresolved_decisions" in result
        and not any("minimum/maximum" in item for item in result["unresolved_decisions"])
    ):
        source = " ".join(linked)
        if not re.search(r"\b(?:delet\w*|remov\w*|purge\w*)\b", source, re.I):
            result["unresolved_decisions"].append(
                "The source gives a retention duration; minimum/maximum interpretation and "
                "deletion timing remain unconfirmed."
            )
    return result, changed


def preserve_section_retention(content: dict, evidence: list[Evidence]) -> dict:
    """Apply the same source-duration contract to complete, supplemental and linked rows."""
    result = deepcopy(content)
    for field in ("requirements", "related_acceptance_criteria"):
        result[field] = [
            preserve_retention_duration(row, evidence)[0] for row in result.get(field, [])
        ]
    return result
