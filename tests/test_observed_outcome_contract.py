"""Shared action-outcome semantics for validation and automatic field repair."""

import pytest
from pydantic import ValidationError, create_model

from cybersrs.atomic_requirements import _repair_field
from cybersrs.evidence import build_evidence
from cybersrs.source_obligations import (
    OBSERVED_OUTCOME_PATTERNS,
    VERBS,
    criterion_target_issues,
    observed_outcome_pattern,
    source_obligations,
)


@pytest.mark.parametrize(
    ("source", "action", "result"),
    [
        (
            "Authorized administrators should assign access permissions.",
            "assign",
            "The corresponding permission state is updated.",
        ),
        (
            "Authorized administrators should inspect access history.",
            "inspect",
            "The requested access history is returned for examination.",
        ),
        (
            "Authorized administrators should review active secret usage.",
            "review",
            "The requested active secret usage is listed for review.",
        ),
        (
            "Authorized administrators should track configuration history.",
            "track",
            "The configuration history is returned for examination.",
        ),
        (
            "Authorized administrators should register secrets.",
            "register",
            "The requested secret is registered and available.",
        ),
        (
            "The system should identify expired exceptions.",
            "identify",
            "The expired exception is identified.",
        ),
        (
            "Authorized administrators should reject exception requests.",
            "reject",
            "The exception request is rejected.",
        ),
    ],
)
def test_prompted_observations_are_accepted_by_the_same_action_contract(
    source: str, action: str, result: str
) -> None:
    """Accept the ordinary external states that operation guidance asks the model to write."""
    unit = next(
        unit
        for unit in source_obligations(build_evidence(source, [])[0])
        if unit.action == action
    )
    criterion = {
        "given": "A controlled source fixture is present",
        "when": f"The authorized administrator initiates the {action} operation",
        "then": result,
    }
    assert not criterion_target_issues(unit, criterion)


def test_every_known_action_reuses_its_validator_pattern_in_native_repair_schema() -> None:
    """Prevent validation and corrective output constraints from drifting independently."""
    for index, (action, pattern) in enumerate(OBSERVED_OUTCOME_PATTERNS.items()):
        schema = create_model(
            f"ActionRepair{index}",
            then=(str, _repair_field("then", f"The system should {action} the item.", action)),
        )
        assert observed_outcome_pattern(action) == pattern
        assert schema.model_json_schema()["properties"]["then"]["pattern"] == (
            f"^[^0-9]*(?:{pattern})[^0-9]*$"
        )


def test_every_functional_parser_action_has_an_observed_outcome_contract() -> None:
    """A newly recognized source verb cannot silently bypass constrained recovery."""
    assert set(VERBS) - {"remain", "be"} <= set(OBSERVED_OUTCOME_PATTERNS)


def test_inspection_repair_requires_the_product_result_not_test_instrumentation() -> None:
    """Replay the failed run without relying on its project-specific wording."""
    schema = create_model(
        "InspectionRepair",
        then=(
            str,
            _repair_field(
                "then",
                "Authorized administrators should inspect access history.",
                "inspect",
            ),
        ),
    )
    with pytest.raises(ValidationError):
        schema.model_validate(
            {"then": "External test capture records the resulting response."}
        )
    assert schema.model_validate(
        {"then": "The requested access history is returned for examination."}
    )


def test_registration_repair_cannot_replace_the_result_with_an_audit_log() -> None:
    """The registered object, rather than a new audit record, is the observed result."""
    schema = create_model(
        "RegistrationRepair",
        then=(
            str,
            _repair_field(
                "then",
                "Authorized administrators should register secrets.",
                "register",
            ),
        ),
    )
    with pytest.raises(ValidationError):
        schema.model_validate(
            {"then": "The secret registration is recorded in the audit log."}
        )
    assert schema.model_validate({"then": "The secret is registered and available."})
