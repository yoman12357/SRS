"""Distinct trust domains and event logging must match their architectural meaning."""

import pytest

from cybersrs.acceptance_grounding import acceptance_logging_issues
from cybersrs.provider import generation_schema
from cybersrs.schemas import ArchitectureComponents
from cybersrs.semantics import mentions_event_logging
from cybersrs.validation import validate_document


@pytest.mark.parametrize(
    "text",
    [
        "A logical access-control component evaluates the request.",
        "An auditor reviews the stated role policy.",
        "The network includes the campus auditorium.",
        "A security operator logs into the dashboard and reviews an alert.",
        "The operator logged into the interface.",
        "The operator is logging into the portal.",
        "The operator logs in and views the alert.",
    ],
)
def test_logical_and_sign_in_wording_is_not_event_logging(text: str) -> None:
    """Reproduce the architecture false positive and ordinary sign-in inflections."""
    assert not mentions_event_logging(text)


@pytest.mark.parametrize(
    "text",
    [
        "The application logs policy changes.",
        "The module performs event logging in JSON.",
        "Events are logged in JSON format.",
        "The logger records audit events.",
    ],
)
def test_real_event_recording_is_still_detected(text: str) -> None:
    """A format preposition is not an authentication action."""
    assert mentions_event_logging(text)


def test_sign_in_source_does_not_authorize_unstated_event_logs() -> None:
    """Correct source-support matching as well as the claim-side false positive."""
    errors = acceptance_logging_issues(
        "Operators log into the dashboard.",
        {
            "then": "The system logs every operator action.",
            "observable_evidence": "Inspect the operator action audit log.",
        },
    )
    assert len(errors) == 2


def test_login_flow_is_not_rejected_as_unrequested_logging(complete_document) -> None:
    """Run the observed sign-in wording through the complete architecture acceptance gate."""
    complete_document.architecture.data_flows[
        0
    ].detail = "A security operator logs into the operations client and reviews an alert."
    report = validate_document(complete_document)
    assert not any("unrequested_logging" in finding.code for finding in report.findings)


def test_trust_boundary_cannot_name_the_same_domain_on_both_sides(complete_document) -> None:
    """Reproduce the policy-engine-to-itself boundary from the live campus draft."""
    boundary = complete_document.architecture.trust_boundaries[0]
    boundary.trusted_component = boundary.untrusted_component
    assert any(
        "trust_boundary_needs_distinct_domains" in finding.code
        for finding in validate_document(complete_document).findings
    )


def test_component_inventory_has_room_for_distinct_boundary_endpoints() -> None:
    """The first constrained stage cannot freeze a single-node impossible boundary roster."""
    schema = generation_schema(ArchitectureComponents, {})
    assert schema["properties"]["items"]["minItems"] == 2


def test_native_boundary_endpoints_are_distinct():
    """The decoder cannot create the repeatedly observed self-boundary graph."""
    from cybersrs.provider import generation_schema
    from cybersrs.schemas import ArchitectureInteractions

    native = generation_schema(
        ArchitectureInteractions, {"architecture_component_names": ["Client", "Service"]}
    )
    cases = native["$defs"]["ArchitectureBoundary"]["anyOf"]
    assert len(cases) == 2
    for case in cases:
        props = case["properties"]
        assert props["untrusted_component"]["const"] not in props["trusted_component"]["enum"]
