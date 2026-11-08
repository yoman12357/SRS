"""Pure preservation of stakeholder scope facts and unresolved decisions."""

import re
from copy import deepcopy

from .evidence import context_evidence_ids
from .schemas import Analysis, Evidence


def preserve_scope_evidence(content: dict, evidence: list[Evidence], analysis: Analysis) -> dict:
    """Project immutable stakeholder scope facts beside model-authored introduction prose."""
    result = deepcopy(content)
    exclusions = {item.evidence_id for item in analysis.assessments if item.kind == "exclusion"}
    context_ids = context_evidence_ids(evidence)
    uncertain = {
        item.evidence_id for item in analysis.assessments if item.kind in {"uncertain", "conflict"}
    }
    uncertain.update(
        item.id
        for item in evidence
        if re.search(
            r"\b(?:is|are|remain|remains)\s+(?:undecided|unknown|unconfirmed|not yet decided)\b|"
            r"\bmust remain open\b",
            item.quote,
            re.I,
        )
    )
    protected = context_ids | exclusions | uncertain
    result["open_issues"] = list(analysis.unresolved_decisions)
    for item in evidence:
        if item.id in uncertain and item.quote not in result["open_issues"]:
            result["open_issues"].append(item.quote)
        for claim in result["items"]:
            if item.id in claim["evidence_ids"] and item.quote == claim["detail"]:
                claim["title"] = (
                    "Out of scope: stakeholder exclusion"
                    if item.id in exclusions
                    else "Unresolved stakeholder decision"
                    if item.id in uncertain
                    else "Stakeholder project context"
                    if item.id in context_ids
                    else f"Stakeholder source statement {item.id}"
                )
                if item.context:
                    claim["title"] += " — response to: " + item.context
                claim["status"] = "unresolved" if item.id in uncertain else "confirmed"
    for item in evidence:
        if item.id not in protected or any(
            item.quote == claim["detail"] and item.id in claim["evidence_ids"]
            for claim in result["items"]
        ):
            continue
        result["items"].append(
            {
                "title": "Out of scope: stakeholder exclusion"
                if item.id in exclusions
                else "Unresolved stakeholder decision"
                if item.id in uncertain
                else "Stakeholder project context",
                "detail": item.quote,
                "status": "unresolved" if item.id in uncertain else "confirmed",
                "evidence_ids": [item.id],
                "sources": [],
            }
        )
        if item.context:
            result["items"][-1]["title"] += " — response to: " + item.context
    return result
