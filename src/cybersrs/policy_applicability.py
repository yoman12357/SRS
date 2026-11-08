"""Recognize explicit stakeholder policy adoption without inferring legal applicability."""

import re


def compliance_requirement_context(requirements: list[dict]) -> list[dict]:
    """Retain every obligation's identity and grounding without unrelated acceptance-test prose."""
    fields = ("id", "statement", "basis", "evidence_ids", "sources")
    return [{key: row[key] for key in fields if key in row} for row in requirements]


def policy_adoption_is_explicit(text: str) -> bool:
    """Require an affirmative adoption/obligation and reject uncertain or denied clauses."""
    for clause in re.split(r"[.;\n]|\bbut\b", text, flags=re.I):
        if re.search(
            r"\b(?:unknown|undecided|unconfirmed|not sure|not required|not mandatory|"
            r"no mandatory|does not apply|not applicable)\b",
            clause,
            re.I,
        ):
            continue
        topic = re.search(
            r"\b(?:policy|framework|standard|regulation|nist|owasp|iso|gdpr|"
            r"hipaa|pci|cis|rfc|ferpa)\b",
            clause,
            re.I,
        )
        adoption = re.search(
            r"\b(?:must|shall)\s+(?:comply|conform|follow|meet|satisfy|implement|adhere)\b|"
            r"^(?:follow|comply|conform|adopt|implement)\b|"
            r"\b(?:policy|framework|standard|regulation)\b.*\b(?:mandatory|required)\b",
            clause.strip(),
            re.I,
        )
        if topic and adoption:
            return True
    return False
