"""Source-bound obligations for independent request decisions and expiration."""

from cybersrs.schemas import Evidence
from cybersrs.source_obligations import criterion_target_issues, source_obligations


def test_permission_choices_keep_separate_obligations_and_the_exact_source() -> None:
    """Reproduce the run that combined approval, rejection and expiration in one test."""
    quote = (
        "A data steward can approve or reject the request, set an expiration date, "
        "and revoke access."
    )
    units = source_obligations(Evidence(id="E-002", source="description", quote=quote))
    assert [unit.action for unit in units] == ["approve", "reject", "set_expiration", "revoke"]
    assert [unit.statement for unit in units] == [
        f"The system shall allow a data steward to {action}."
        for action in (
            "approve the request", "reject the request", "set an expiration date", "revoke access"
        )
    ]
    assert all(unit.quote == quote and unit.evidence_id == "E-002" for unit in units)


def test_product_purpose_keeps_the_actor_and_request_verb() -> None:
    """A brief that uses 'lets' still produces a grammatical permission statement."""
    fact = Evidence(
        id="E-001",
        source="description",
        quote=(
            "Design a system that lets university researchers request "
            "permission to share a dataset."
        ),
    )
    unit, = source_obligations(fact)
    assert unit.statement == (
        "The system shall allow university researchers to request permission to share a dataset."
    )


def test_expiration_update_is_an_observed_result() -> None:
    """Recognize the persisted expiration result, including verb-first wording."""
    fact = Evidence(
        id="E-002", source="description",
        quote="A data steward can set an expiration date.",
    )
    unit, = source_obligations(fact)
    assert criterion_target_issues(unit, {
        "given": "A data steward reviews a dataset sharing request",
        "when": "The data steward sets an expiration date using a fixture date",
        "then": "The system updates the expiration to match the provided fixture date value",
        "method": "test",
        "observable_evidence": "External test capture of the resulting state",
    }) == []
