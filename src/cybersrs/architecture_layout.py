"""Render model-chosen logical layout using unchanged canonical source obligations."""

from __future__ import annotations

import re

from .schemas import Evidence


def source_unknowns(evidence: list[Evidence]) -> list[str]:
    """Keep exact unresolved source passages without reopening explicit exclusions."""
    return list(
        dict.fromkeys(
            fact.quote
            for fact in evidence
            if re.search(
                r"\b(?:undecided|unknown|unspecified|unconfirmed|not yet decided)\b",
                fact.quote,
                re.I,
            )
        )
    )


def _links(ids: list[str], canonical: dict[str, dict]) -> dict:
    """Preserve canonical evidence and literal source citations without model-authored metadata."""
    rows = [canonical[rid] for rid in ids]
    citations = {
        (citation["chunk_id"], citation["quote"]): citation
        for row in rows
        for citation in row["sources"]
    }
    return {
        "status": "proposed",
        "requirement_ids": list(dict.fromkeys(ids)),
        "evidence_ids": sorted({eid for row in rows for eid in row["evidence_ids"]}),
        "sources": list(citations.values()),
    }


def canonical_responsibility(ids: list[str], canonical: dict[str, dict]) -> str:
    """Use the assigned normative statements without adding controls or implementation facts."""
    return " ".join(canonical[rid]["statement"] for rid in dict.fromkeys(ids))


def render_component_layout(placements: list[dict], canonical: dict[str, dict]) -> list[dict]:
    """Render the model's grouping while preserving the exact canonical responsibility text."""
    return [
        _links(item["requirement_ids"], canonical)
        | {
            "title": item["component_name"],
            "component_name": item["component_name"],
            "detail": "Proposed logical owner for " + ", ".join(item["requirement_ids"]) + ".",
            "responsibility": canonical_responsibility(item["requirement_ids"], canonical),
        }
        for item in placements
    ]


def render_interaction_layout(
    placement: dict,
    canonical: dict[str, dict],
    access_contracts: list[dict] | None = None,
) -> dict:
    """Compose source-backed interaction and enforcement views of model-chosen endpoint pairs."""
    flows, boundaries = [], []
    for item in placement["data_flows"]:
        target = next(
            (
                contract
                for contract in access_contracts or []
                if contract["resource_component"] == item["to_component"]
                and set(contract["requirement_ids"]) & set(item["requirement_ids"])
            ),
            None,
        )
        prefix = (
            {
                "denied": "Denied access attempt. ",
                "permitted": "Permitted access decision. ",
                "authenticated": "Authentication-gated access decision. ",
            }.get(target["outcome"], "")
            if target
            else ""
        )
        flows.append(
            _links(item["requirement_ids"], canonical)
            | {
                "title": "Proposed source-defined interaction",
                "detail": "Proposed directed path for " + ", ".join(item["requirement_ids"]) + ".",
                "from_component": item["from_component"],
                "to_component": item["to_component"],
                "data_or_action": prefix
                + canonical_responsibility(item["requirement_ids"], canonical),
            }
        )
    for item in placement["trust_boundaries"]:
        boundaries.append(
            _links(item["requirement_ids"], canonical)
            | {
                "title": "Proposed source-defined trust boundary",
                "detail": "Proposed logical trust-domain crossing for "
                + ", ".join(item["requirement_ids"])
                + ".",
                "untrusted_component": item["untrusted_component"],
                "trusted_component": item["trusted_component"],
                "enforcement": canonical_responsibility(item["requirement_ids"], canonical),
            }
        )
    return {"data_flows": flows, "trust_boundaries": boundaries}
