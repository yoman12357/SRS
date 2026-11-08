"""Measured retention-bound failures are corrected without changing source decisions."""

import pytest

from cybersrs.quantity_normalization import preserve_retention_duration
from cybersrs.schemas import Evidence


def test_bare_duration_keeps_values_and_criteria_with_an_open_policy_decision() -> None:
    """Restore the exact stated duration while retaining model-authored test outcomes."""
    evidence = [Evidence(id="E-1", source="description", quote="Retain audit records for 30 days.")]
    original = {
        "evidence_ids": ["E-1"],
        "statement": "Retain records for a minimum of 30 days.",
        "rationale": "The source specifies a minimum of 30 days.",
        "acceptance_criteria": [
            {
                "given": "A change is recorded",
                "when": "Inspect records",
                "then": "The record is retained for at least 30 days.",
                "observable_evidence": "Dated audit record",
            }
        ],
        "unresolved_decisions": [],
    }
    result, changed = preserve_retention_duration(original, evidence)
    assert changed and result["statement"] == "Retain records for 30 days."
    assert result["acceptance_criteria"][0]["then"] == "The record is retained for 30 days."
    assert result["acceptance_criteria"][0]["given"] == original["acceptance_criteria"][0]["given"]
    assert result["unresolved_decisions"] and original["unresolved_decisions"] == []


def test_confirmed_source_bound_is_never_removed() -> None:
    """An explicit minimum cannot be converted into an unqualified or maximum duration."""
    evidence = [
        Evidence(id="E-1", source="description", quote="Retain records for a minimum of 30 days.")
    ]
    original = {
        "evidence_ids": ["E-1"],
        "statement": "Retain records for a minimum of 30 days.",
        "acceptance_criteria": [],
        "unresolved_decisions": [],
    }
    assert preserve_retention_duration(original, evidence) == (original, False)


@pytest.mark.parametrize(
    "bound", ["a minimum period of", "a minimum retention period of", "a maximum duration of"]
)
def test_duration_bound_variants_preserve_bare_source_and_explicit_bound(bound):
    """The actual minimum-period paraphrase is as unsupported as an added 'at least'."""
    from cybersrs.semantics import semantic_issues

    source = Evidence(id="E-001", source="description", quote="Retain audit records for 30 days.")
    statement = f"The system shall retain audit records for {bound} 30 days."
    row = {"statement": statement, "evidence_ids": [source.id], "acceptance_criteria": []}
    fixed, changed = preserve_retention_duration(row, [source])
    assert changed and fixed["statement"] == "The system shall retain audit records for 30 days."
    assert semantic_issues(statement, [source]) == ["E-001:unconfirmed_duration_bound"]
    bounded_source = source.model_copy(update={"quote": statement})
    assert preserve_retention_duration(row, [bounded_source]) == (row, False)
