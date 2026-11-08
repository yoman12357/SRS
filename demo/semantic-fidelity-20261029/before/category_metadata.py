"""Factual explanations for categories with no uncovered source obligation."""

import re

from .schemas import REQUIREMENT_PREFIXES, RequirementsSection

CATEGORY_METADATA_VERSION = "canonical-category-metadata-1.1"


def canonical_category_ids(name: str, requirements: list[dict]) -> list[str]:
    """Index explicit canonical topics/dimensions without using generated titles or rationale."""
    if name not in REQUIREMENT_PREFIXES:
        raise ValueError("unknown_requirement_category")
    dimensions = {
        "nonfunctional": {"performance", "availability"},
        "security": {"security", "privacy", "compliance", "auditability"},
        "data": {"data"},
    }.get(name, set())
    patterns = {
        "network": r"\b(?:network\w*|internet|firewalls?|vpn|subnets?|vlans?|routing|"
        r"bandwidth|ethernet|wireless|segmentation|packets?)\b",
        "data": r"\b(?:retain\w*|retention|records?|logs?|stor\w*|delet\w*|purg\w*)\b",
        "nonfunctional": r"\b(?:latency|throughput|availability|uptime|"
        r"(?:simultaneous|concurrent)\s+(?:sessions?|users?|connections?))\b",
    }
    return sorted(
        {
            row["id"]
            for row in requirements
            if dimensions & set(row.get("dimensions", []))
            or (name in patterns and re.search(patterns[name], row.get("statement", ""), re.I))
        }
    )


def empty_category_metadata(
    name: str, relevant: list[dict], available: list[dict] | None = None
) -> dict:
    """Explain only actual canonical coverage, without authoring new product behavior."""
    if name not in REQUIREMENT_PREFIXES:
        raise ValueError("unknown_requirement_category")
    catalog = available if available is not None else relevant
    required = sorted({row["id"] for row in relevant} | set(canonical_category_ids(name, catalog)))
    ids = sorted({row["id"] for row in (available if available is not None else relevant)})
    if any(not value for value in ids + required) or set(required) - set(ids):
        raise ValueError("canonical_requirement_ids_required")
    return {
        "applicability_reason": (
            "Existing canonical requirements, where applicable, are linked below; "
            "this section adds no separate obligation. "
            "Unresolved stakeholder decisions remain open."
        ),
        "available_requirement_ids": ids,
        "required_requirement_ids": required,
    }


def validate_empty_category_index(candidate: RequirementsSection, metadata: dict) -> list[str]:
    """Require the factual explanation and complete known links without new behavior or tests."""
    if candidate.requirements:
        return ["no_uncovered_source_obligation_for_new_requirement"]
    if (
        candidate.applicability_reason != metadata["applicability_reason"]
        or set(candidate.related_requirement_ids) - set(metadata["available_requirement_ids"])
        or set(metadata["required_requirement_ids"]) - set(candidate.related_requirement_ids)
        or len(candidate.related_requirement_ids) != len(set(candidate.related_requirement_ids))
        or candidate.related_acceptance_criteria
    ):
        return ["empty_category_metadata_must_match_canonical_coverage"]
    return []
