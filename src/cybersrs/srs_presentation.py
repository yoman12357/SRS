"""Concise IEEE 830 presentation of canonical requirements, without new product claims."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import Field

from .architecture_sources import source_actor_contracts
from .clarification_policy import deduplicate_decisions
from .schemas import Citation, Document, Requirement, StrictModel
from .source_detail_policy import nonhuman_role_modifier

PRESENTATION_PROFILE = "ieee-830-1998-1.0"
FORMAT_REFERENCE = "IEEE Std 830-1998, clauses 5 and Annex A (document organization)."


class ReportTable(StrictModel):
    """Small human-readable table shared by the browser, PDF and Markdown."""

    columns: list[str]
    rows: list[list[str]]


class ReportRequirement(StrictModel):
    """Normative reader view; full criteria and rationale stay in canonical content."""

    id: str
    statement: str
    priority: Literal["must", "should", "could"]
    basis: Literal["explicit", "derived", "proposed"]
    sources: list[Citation]
    evidence_ids: list[str]
    test_ids: list[str] = Field(default_factory=list)


class ReportSection(StrictModel):
    """Numbered section containing only selected, source-preserving report content."""

    number: str
    title: str
    paragraphs: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    tables: list[ReportTable] = Field(default_factory=list)
    requirements: list[ReportRequirement] = Field(default_factory=list)


class SRSPresentation(StrictModel):
    """Derived reader view; canonical JSON and its approval hash remain unchanged."""

    profile: Literal["ieee-830-1998-1.0"] = PRESENTATION_PROFILE
    title: str
    sections: list[ReportSection]


def stakeholder_table(document: Document) -> ReportTable:
    """Simplify role labels while retaining source classes and distinct authority."""
    source = " ".join(item.quote for item in document.evidence)
    groups = {
        "User": r"\b(?:students?|faculty|(?:authorized )?(?:university )?staff|"
        r"researchers?|guests?|employees?|contractors?|(?:campus )?visitors?|users?)\b",
        "Admin": r"\b(?:(?:network|lab|laboratory|university|system)\s+)?"
        r"(?:administrators?|admins?)\b|\badministrative\s+(?:users?|staff)\b",
        "Analyst": r"\b(?:security\s+)?analysts?\b",
        "Operator": r"\b(?:(?:security|support|network)\s+)?operators?\b",
    }
    rows = []
    represented = set()
    admin_spans = [match.span() for match in re.finditer(groups["Admin"], source, re.I)]
    for label, pattern in groups.items():
        literals = []
        for match in re.finditer(pattern, source, re.I):
            if nonhuman_role_modifier(source, match.start(), match.end()):
                continue
            if label == "User" and any(start <= match.start() < end for start, end in admin_spans):
                continue
            if match[0].casefold().rstrip("s") not in {
                value.casefold().rstrip("s") for value in literals
            }:
                literals.append(match[0])
        if label == "User" and any(value.casefold() not in {"user", "users"} for value in literals):
            literals = [value for value in literals if value.casefold() not in {"user", "users"}]
        if not literals:
            continue
        represented.update(value.casefold().rstrip("s") for value in literals)
        responsibility = (
            "Uses permitted functions; each source class keeps its specified permissions."
            if label == "User"
            else "Performs only the role's source-defined operations in section 3."
        )
        rows.append([label, ", ".join(literals), responsibility])
    obligations = [
        row.model_dump(include={"id", "statement", "evidence_ids"})
        for row in _requirements(document)
    ]
    actors = document.analysis.stakeholders + [
        contract["actor"] for contract in source_actor_contracts(document.evidence, obligations)
    ]
    for actor in actors:
        literal = re.sub(r"^(?:the|a|an|only)\s+", "", actor.strip(), flags=re.I)
        key = literal.casefold().rstrip("s")
        if not key or key in represented:
            continue
        for match in re.finditer(rf"\b{re.escape(literal)}\b", source, re.I):
            if not nonhuman_role_modifier(source, match.start(), match.end()):
                represented.add(key)
                rows.append([match[0], match[0], "See the source-defined scope and requirements."])
                break
    rows.append(
        [
            "Project Analyst",
            "Document review role",
            "Reviews requirements and tracks open decisions; this role grants no product access.",
        ]
    )
    return ReportTable(columns=["Role", "Source user groups", "Responsibility"], rows=rows)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value.strip()))


def _requirements(document: Document) -> list[Requirement]:
    return [
        row
        for name in ("functional", "nonfunctional", "security", "data", "network")
        for row in getattr(document, name).requirements
    ]


def _function_index(rows: list[Requirement]) -> list[str]:
    """Index source-present functional topics; complete obligations stay in section 3."""
    return [
        row.statement.removeprefix("The system shall ").rstrip(".") + " - " + row.id for row in rows
    ]


def build_srs_presentation(document: Document) -> SRSPresentation:
    """Organize every canonical requirement once in the requested IEEE 830 outline."""
    sections: list[ReportSection] = []

    def add(number: str, title: str, **content) -> ReportSection:
        if "requirements" in content:
            content["requirements"] = [
                ReportRequirement.model_validate(
                    row.model_dump(
                        include={"id", "statement", "priority", "basis", "sources", "evidence_ids"}
                    )
                    | {
                        "test_ids": [
                            test.id
                            for test in document.verification.tests
                            if row.id in test.requirement_ids
                        ]
                    }
                )
                for row in content["requirements"]
            ]
        section = ReportSection(number=number, title=title, **content)
        sections.append(section)
        return section

    rows = _requirements(document)
    behavioral_ids = set(document.functional.related_requirement_ids)
    functional_rows = list(document.functional.requirements) + [
        row
        for row in rows
        if row.id in behavioral_ids
        and row.id not in {item.id for item in document.functional.requirements}
    ]
    add("1", "Introduction")
    add(
        "1.1",
        "Purpose",
        paragraphs=[
            document.introduction.summary,
            "This SRS describes the software's required behavior for users, administrators and "
            "the Project Analyst reviewing the specification.",
        ],
    )
    add("1.2", "Scope", paragraphs=[document.original_description])
    glossary = [[item.title, item.detail] for item in document.glossary.items]
    add(
        "1.3",
        "Definitions, acronyms and abbreviations",
        tables=[ReportTable(columns=["Term", "Meaning"], rows=glossary)] if glossary else [],
        paragraphs=[] if glossary else ["No project-specific terms were supplied."],
    )
    reference_rows = [["Format", FORMAT_REFERENCE]]
    used_chunks = {citation.chunk_id for row in rows for citation in row.sources}
    for source in document.sources:
        if source.id in used_chunks:
            reference_rows.append(
                [
                    source.id,
                    f"{source.title}; document {source.source_document_id}; "
                    f"chunk {source.chunk_index}; {source.page_or_section}; "
                    f"relevance {source.relevance_score:g}",
                ]
            )
    add(
        "1.4",
        "References",
        tables=[ReportTable(columns=["Reference", "Source"], rows=reference_rows)],
    )
    add(
        "1.5",
        "Overview",
        paragraphs=[
            "Section 2 summarizes the product, stakeholders and open decisions. Section 3 "
            "contains the uniquely identified requirements. Appendices A–D cover threat "
            "hypotheses, risk assessment, the proposed SDLC and verification procedures.",
        ],
    )
    add("2", "Overall description")
    add(
        "2.1",
        "Product perspective",
        paragraphs=[document.original_description.split(". ", 1)[0].rstrip(".") + "."],
    )
    functions = _function_index(functional_rows)
    add(
        "2.2",
        "Product functions",
        bullets=functions,
        paragraphs=[
            "Functional topics are summarized below; section 3 retains the full requirements."
        ]
        if functions
        else ["Product functions require stakeholder clarification."],
    )
    characteristics = [
        item.quote
        for item in document.evidence
        if re.search(
            r"\b(?:training|trained|education|experience|expertise|novice)\b", item.quote, re.I
        )
    ]
    add(
        "2.3",
        "User characteristics and stakeholders",
        tables=[stakeholder_table(document)],
        paragraphs=["Labels group stakeholders for readability. They do not combine permissions. "]
        + (
            characteristics
            or ["Education, training and experience requirements remain unspecified."]
        ),
    )
    constraints = [
        item.quote
        for item in document.evidence
        if any(
            assessment.evidence_id == item.id and assessment.kind in {"constraint", "exclusion"}
            for assessment in document.analysis.assessments
        )
    ]
    add(
        "2.4",
        "Constraints",
        bullets=_unique(constraints),
        paragraphs=[]
        if constraints
        else [
            "No additional implementation constraints were confirmed. Source-defined restrictions "
            "remain in the requirements in section 3.",
        ],
    )
    unknowns = deduplicate_decisions(
        document.analysis.unresolved_decisions
        + document.introduction.open_issues
        + [question.question for question in document.analysis.questions]
        + [decision for row in rows for decision in row.unresolved_decisions]
        + document.compliance.open_decisions,
        document.evidence,
        include_references=False,
    )
    add(
        "2.5",
        "Assumptions and dependencies",
        bullets=unknowns,
        paragraphs=[
            "Open decisions requiring confirmation:"
            if unknowns
            else "No additional assumptions or dependencies were confirmed in the supplied brief.",
        ],
    )
    add(
        "3",
        "Specific requirements",
        paragraphs=[
            "Each requirement is stated once with its original identifier and wording. "
            "Cross-references identify requirements covering more than one concern.",
        ],
    )
    add("3.1", "External interface requirements")
    interface_patterns = {
        "3.1.1": ("User interfaces", r"\b(?:dashboard|interface|portal|console|users?)\b"),
        "3.1.2": ("Hardware interfaces", r"\b(?:hardware|devices?|equipment|sensors?)\b"),
        "3.1.3": (
            "Software interfaces",
            r"\b(?:integrat\w*|authentication|external systems?|directory)\b",
        ),
        "3.1.4": (
            "Communications interfaces",
            r"\b(?:networks?|DNS|VPN|protocols?|wired|wireless)\b",
        ),
    }
    for number, (title, pattern) in interface_patterns.items():
        links = [row.id for row in rows if re.search(pattern, row.statement, re.I)]
        add(
            number,
            title,
            paragraphs=[
                "Related requirements: " + ", ".join(links) + ". Interface details beyond those "
                "requirements remain unspecified."
                if links
                else "No specific interface requirement was supplied; confirmation is required.",
            ],
            requirements=[
                row for row in document.network.requirements if row.id not in behavioral_ids
            ]
            if number == "3.1.4"
            else [],
        )
    buckets = {
        "3.2": functional_rows,
        "3.3": [],
        "3.4": [row for row in document.data.requirements if row.id not in behavioral_ids],
        "3.5": [],
        "3.6.1": [],
        "3.6.2": [],
        "3.6.3": [row for row in document.security.requirements if row.id not in behavioral_ids],
        "3.6.4": [],
        "3.6.5": [],
        "3.7": [],
    }
    for row in document.nonfunctional.requirements:
        if row.id in behavioral_ids:
            continue
        text = row.statement
        target = (
            "3.3"
            if re.search(
                r"\b(?:performance|scal\w*|latency|throughput|concurrent|response time)\b",
                text,
                re.I,
            )
            else next(
                (
                    target
                    for target, pattern in (
                        ("3.6.3", r"\bsecur\w*\b"),
                        ("3.6.2", r"\b(?:availab\w*|uptime)\b"),
                        ("3.6.4", r"\b(?:maintainab\w*|manageab\w*)\b"),
                        ("3.6.5", r"\bportab\w*\b"),
                        ("3.6.1", r"\breliab\w*\b"),
                    )
                    if re.search(pattern, text, re.I)
                ),
                "3.7",
            )
        )
        buckets[target].append(row)
    headings = [
        ("3.2", "Functional requirements"),
        ("3.3", "Performance requirements"),
        ("3.4", "Logical database requirements"),
        ("3.5", "Design constraints"),
        ("3.6", "Software system attributes"),
        ("3.6.1", "Reliability"),
        ("3.6.2", "Availability"),
        ("3.6.3", "Security"),
        ("3.6.4", "Maintainability"),
        ("3.6.5", "Portability"),
        ("3.7", "Other requirements"),
    ]
    attribute_patterns = {
        "3.6.1": r"\breliab\w*\b",
        "3.6.2": r"\b(?:availab\w*|uptime)\b",
        "3.6.3": r"\b(?:secur\w*|authenticat\w*|permissions?|restrict\w*|audit)\b",
        "3.6.4": r"\b(?:maintainab\w*|manageab\w*)\b",
        "3.6.5": r"\bportab\w*\b",
    }
    for number, title in headings:
        if number == "3.6":
            add(number, title)
            continue
        assigned = buckets[number]
        linked = [
            row.id
            for row in rows
            if row not in assigned
            and re.search(attribute_patterns.get(number, r"(?!)"), row.statement, re.I)
        ]
        paragraphs = ["Also covered by: " + ", ".join(linked) + "."] if linked else []
        if not assigned and not linked:
            paragraphs.append("No separate requirement was specified in the supplied brief.")
        policies = (
            [
                f"{mapping.applicability.capitalize()}: {mapping.framework_or_policy} "
                f"{mapping.control_or_section}. {mapping.rationale} "
                f"Related requirements: {', '.join(mapping.requirement_ids)}."
                for mapping in document.compliance.mappings
            ]
            if number == "3.5"
            else []
        )
        if policies:
            paragraphs = []
        add(number, title, requirements=assigned, paragraphs=paragraphs, bullets=policies)
    _assessment_appendices(document, add)
    add(
        "D",
        "Verification and acceptance",
        paragraphs=[
            "These procedures define how to verify the requirements. Execution results "
            "are recorded during implementation and acceptance."
        ],
        bullets=document.verification.limitations,
    )
    for index, test in enumerate(document.verification.tests, 1):
        add(
            f"D.{index}",
            f"{test.id} · {', '.join(test.requirement_ids)}",
            paragraphs=[
                *test.procedure,
                test.expected_result if test.expected_result.startswith("Expected: ")
                else f"Expected outcome — {test.expected_result}",
                test.evidence_to_record if test.evidence_to_record.startswith("Evidence: ")
                else f"Evidence to record — {test.evidence_to_record}",
            ],
        )
    return SRSPresentation(title=document.title, sections=sections)


def _assessment_appendices(document: Document, add) -> None:
    """Expose existing cyber assessments and lifecycle evidence without changing content."""
    add(
        "A",
        "Derived threat hypotheses",
        paragraphs=document.threats.assumptions
        + [
            "These are planning hypotheses, not observed incidents or additional approved controls."
        ],
    )
    if not document.threats.threats:
        add(
            "A.1",
            "Threat assessment pending",
            paragraphs=[
                "This saved version has no threat hypotheses. A new generation is needed to "
                "populate this assessment; existing versions are not silently changed."
            ],
        )
    for index, threat in enumerate(document.threats.threats, 1):
        add(
            f"A.{index}",
            f"{threat.id}: {threat.asset}",
            paragraphs=[
                "Scenario: " + threat.scenario,
                "Hypothetical actor or cause: " + threat.actor,
                "Potential consequence: " + threat.impact,
                "Linked requirements: " + ", ".join(threat.control_requirement_ids),
                "Original evidence: " + ", ".join(threat.evidence_ids),
                "Residual exposure: " + threat.residual_risk,
            ],
            bullets=[f"Source {s.chunk_id}: {s.quote}" for s in threat.sources],
        )
    add(
        "B",
        "Risk assessment",
        paragraphs=[
            "Risk treatments are proposals for review. Unknown likelihood and impact ratings "
            "mean unassessed; no numeric confidence or severity is inferred."
        ],
        bullets=document.risks.open_issues,
    )
    if not document.risks.risks:
        add(
            "B.1",
            "Risk assessment pending",
            paragraphs=[
                "This saved version contains no risk assessment. Existing content is preserved."
            ],
        )
    for index, risk in enumerate(document.risks.risks, 1):
        add(
            f"B.{index}",
            risk.id,
            paragraphs=[
                risk.description,
                f"Likelihood: {risk.likelihood}; impact: {risk.impact}; owner: {risk.owner}.",
                "Rationale: " + risk.rationale,
                "Proposed treatment: " + risk.mitigation,
                "Linked requirements: " + ", ".join(risk.requirement_ids),
                "Original evidence: " + ", ".join(risk.evidence_ids),
            ],
        )
    workflow = document.sdlc
    add(
        "C",
        "SDLC recommendation and delivery workflow",
        paragraphs=[
            "Proposed lifecycle: " + workflow.selected_model,
            workflow.justification,
            "Recommendation requires human confirmation of delivery constraints and team capacity. "
            "Suitability points are deterministic rule scores, not probabilities.",
            "Policy version: " + document.sdlc_policy_version,
            "Unconfirmed decision factors: "
            + ", ".join(factor.replace("_", " ") for factor in workflow.unknown_factors),
        ],
        bullets=workflow.tradeoffs,
    )
    add(
        "C.1",
        "Ranking and source evidence",
        tables=[
            ReportTable(
                columns=["Candidate", "Suitability points"],
                rows=[[c.model, str(c.score)] for c in document.sdlc_candidates],
            )
        ],
        bullets=[
            f"{f.name} = {f.value} ({f.basis}). {f.rationale} "
            f"Original evidence: {', '.join(f.evidence_ids)}."
            for f in document.sdlc_factors
        ],
    )
    for index, candidate in enumerate(document.sdlc_candidates, 1):
        add(f"C.1.{index}", candidate.model + " suitability reasons", bullets=candidate.reasons)
    add(
        "C.2",
        "Methodology phases",
        paragraphs=[
            "Activities reference the canonical requirements and proposed verification work. "
            "Human gates are pending decisions, not approval records."
        ],
    )
    for index, phase in enumerate(workflow.phases, 1):
        add(
            f"C.2.{index}",
            phase.name,
            paragraphs=[
                "Proposed roles: " + "; ".join(phase.roles),
                "Linked requirements: " + ", ".join(phase.requirement_ids),
                "Human gate: " + phase.human_approval,
            ],
            bullets=[
                f"{label}: {item}"
                for label, values in (
                    ("Activity", phase.activities),
                    ("Deliverable", phase.deliverables),
                    ("Entry criterion", phase.entry_criteria),
                    ("Exit criterion", phase.exit_criteria),
                    ("Security check", phase.security_checks),
                )
                for item in values
            ],
        )
    if workflow.verification_pairs:
        add(
            "C.3",
            "Development and verification pairing",
            bullets=[
                f"{pair.development_phase} -> {pair.verification_phase} ({pair.test_scope}): "
                f"{pair.test_plan_deliverable}. Requirements: {', '.join(pair.requirement_ids)}."
                for pair in workflow.verification_pairs
            ],
        )
