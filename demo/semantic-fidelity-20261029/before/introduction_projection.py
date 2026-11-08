"""An exact source-fact introduction with no newly asserted product commitments."""

from .schemas import Analysis, Evidence, NarrativeSection, SourceIntroductionPlan
from .source_facts import preserve_scope_evidence

INTRODUCTION_PROJECTION_VERSION = "source-fact-introduction-1.0"
SOURCE_FACT_OVERVIEW = (
    "This specification records the project purpose, stakeholder constraints and "
    "unresolved decisions stated in the source evidence below."
)


def validate_introduction_order(
    plan: SourceIntroductionPlan, evidence: list[Evidence]
) -> list[str]:
    """Reject unknown, repeated or omitted source facts independently of native decoding."""
    known = {item.id for item in evidence}
    errors = []
    if len(set(plan.evidence_order)) != len(plan.evidence_order):
        errors.append("introduction:duplicate_source_fact")
    if set(plan.evidence_order) - known:
        errors.append("introduction:unknown_source_fact")
    if known - set(plan.evidence_order):
        errors.append("introduction:missing_source_fact")
    return errors


def compose_introduction(
    plan: SourceIntroductionPlan, evidence: list[Evidence], analysis: Analysis
) -> dict:
    """Preserve exact fact/answer text and source status in the model's chosen order."""
    errors = validate_introduction_order(plan, evidence)
    if errors:
        raise ValueError(";".join(errors))
    by_id = {item.id: item for item in evidence}
    content = {
        "summary": SOURCE_FACT_OVERVIEW,
        "items": [
            {
                "title": f"Stakeholder source statement {eid}",
                "detail": by_id[eid].quote,
                "status": "confirmed",
                "evidence_ids": [eid],
                "sources": [],
                "requirement_ids": [],
            }
            for eid in plan.evidence_order
        ],
        "open_issues": [],
    }
    content = preserve_scope_evidence(content, evidence, analysis)
    for item in content["items"]:
        fact = by_id[item["evidence_ids"][0]]
        if fact.context:
            item["title"] += " — response to: " + fact.context
    return NarrativeSection.model_validate(content).model_dump()


def introduction_projection_issues(
    content: dict, evidence: list[Evidence], analysis: Analysis
) -> list[str]:
    """Recheck a claimed automatic view against exact current input, including decision status."""
    if any(len(item["evidence_ids"]) != 1 for item in content["items"]):
        return ["introduction:source_projection_mismatch"]
    plan = SourceIntroductionPlan(
        evidence_order=[item["evidence_ids"][0] for item in content["items"]]
    )
    errors = validate_introduction_order(plan, evidence)
    if errors:
        return errors
    if content != compose_introduction(plan, evidence, analysis):
        return ["introduction:source_projection_mismatch"]
    return []
