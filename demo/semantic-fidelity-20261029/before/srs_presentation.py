"""Concise IEEE 830 presentation of canonical requirements, without new product claims."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import Field

from .schemas import Citation, Document, Requirement, StrictModel

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
        "User": r"\b(?:students?|faculty|staff|researchers?|guests?|employees?|"
        r"contractors?|users?)\b",
        "Admin": r"\b(?:(?:network|lab|laboratory|university|system)\s+)?"
        r"(?:administrators?|admins?)\b|\badministrative\s+(?:users?|staff)\b",
        "Analyst": r"\b(?:security\s+)?analysts?\b",
        "Operator": r"\b(?:(?:security|support|network)\s+)?operators?\b",
    }
    rows = []
    admin_spans = [match.span() for match in re.finditer(groups["Admin"], source, re.I)]
    for label, pattern in groups.items():
        literals = []
        for match in re.finditer(pattern, source, re.I):
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
        responsibility = (
            "Uses permitted functions; each source class keeps its specified permissions."
            if label == "User"
            else "Performs only the role's source-defined operations in section 3."
        )
        rows.append([label, ", ".join(literals), responsibility])
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
    topics = [
        ("Access permissions", r"\b(?:access|permissions?|authoriz\w*)\b"),
        ("DNS and web filtering", r"\b(?:DNS|domains?|web.access|filtering)\b"),
        ("Authentication", r"\b(?:authenticat\w*|log.in|MFA)\b"),
        ("Policy controls", r"\bpolic(?:y|ies)\b"),
        ("Monitoring and alerts", r"\b(?:monitor\w*|alerts?)\b"),
        ("Dashboard", r"\bdashboards?\b"),
        ("Event investigation", r"\binvestigat\w*\b"),
        ("Audit logging", r"\b(?:audit|logs?|logging)\b"),
        ("Network isolation", r"\b(?:isolat\w*|segment\w*)\b"),
        ("Device support", r"\bdevices?\b"),
    ]
    result, indexed = [], set()
    for title, pattern in topics:
        linked = [row.id for row in rows if re.search(pattern, row.statement, re.I)]
        if linked:
            result.append(title + " — " + ", ".join(linked))
            indexed.update(linked)
    result.extend(row.title + " — " + row.id for row in rows if row.id not in indexed)
    return result


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
            "contains the uniquely identified requirements. Detailed evidence, acceptance "
            "procedures and the SDLC plan are available in the supporting report.",
        ],
    )
    add("2", "Overall description")
    add(
        "2.1",
        "Product perspective",
        paragraphs=[document.original_description.split(". ", 1)[0].rstrip(".") + "."],
    )
    functions = _function_index(document.functional.requirements)
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
    unknowns = _unique(
        document.analysis.unresolved_decisions
        + document.introduction.open_issues
        + [question.question for question in document.analysis.questions]
        + [decision for row in rows for decision in row.unresolved_decisions]
        + document.compliance.open_decisions
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
            requirements=list(document.network.requirements) if number == "3.1.4" else [],
        )
    buckets = {
        "3.2": list(document.functional.requirements),
        "3.3": [],
        "3.4": list(document.data.requirements),
        "3.5": [],
        "3.6.1": [],
        "3.6.2": [],
        "3.6.3": list(document.security.requirements),
        "3.6.4": [],
        "3.6.5": [],
        "3.7": [],
    }
    for row in document.nonfunctional.requirements:
        text = row.statement
        target = (
            "3.3"
            if re.search(
                r"\b(?:performance|scal\w*|latency|throughput|concurrent|response time)\b",
                text,
                re.I,
            )
            else ("3.6.3" if re.search(r"\bsecur\w*\b", text, re.I) else "3.6.1")
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
    return SRSPresentation(title=document.title, sections=sections)
