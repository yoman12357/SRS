"""Source meaning must survive shared context and section generation."""

import pytest

from cybersrs.schemas import Evidence
from cybersrs.semantics import semantic_issues


@pytest.mark.parametrize(
    "source,wrong,right",
    [
        (
            "The planning population is 2000 registered devices; concurrency is undecided.",
            "The system shall support 2000 concurrent devices.",
            "The system shall account for 2000 registered devices.",
        ),
        (
            "Plan for 250 registered users and 25 simultaneous sessions.",
            "The system shall support 250 simultaneous sessions.",
            "The system shall support 25 simultaneous sessions.",
        ),
        (
            "Retain audit logs for 30 days.",
            "The response latency shall be 30 days.",
            "The system shall retain audit logs for 30 days.",
        ),
        (
            "Do not automatically isolate devices.",
            "The system shall automatically isolate devices.",
            "The system shall not automatically isolate devices.",
        ),
    ],
)
def test_recognized_source_relationships_are_not_swapped(source, wrong, right):
    """Matching the same number or action token is insufficient grounding."""
    evidence = [Evidence(id="E-001", source="description", quote=source)]
    assert semantic_issues(wrong, evidence)
    assert not semantic_issues(right, evidence)


def test_active_capacity_cap_cannot_be_inferred_from_planning_inventory():
    """Catch a real generated error even when the number precedes no concurrency adjective."""
    evidence = [
        Evidence(
            id="E-001",
            source="description",
            quote=(
                "The planning population is 2000 registered devices; "
                "concurrency is not yet decided."
            ),
        )
    ]
    assert semantic_issues(
        "The system shall track active device count, with recorded values not exceeding 2000.",
        evidence,
    )


@pytest.mark.parametrize(
    "claim",
    [
        "The planned capacity is 250 registered users with 25 simultaneous active sessions.",
        "Plan for 250 registered users and 25 simultaneous sessions.",
        "There are 250 registered users; the active user capacity remains undecided.",
    ],
)
def test_separate_planning_and_session_quantities_are_not_combined(claim):
    """A real VPN introduction must not bind the population to another session figure."""
    evidence = [
        Evidence(
            id="E-006",
            source="description",
            quote="Plan for 250 registered users and 25 simultaneous sessions.",
        )
    ]
    assert not semantic_issues(claim, evidence)


def test_population_still_cannot_be_used_as_an_indirect_active_limit():
    """Narrower quantity binding continues to reject an actual invented active-user cap."""
    evidence = [
        Evidence(
            id="E-006",
            source="description",
            quote="Plan for 250 registered users and 25 simultaneous sessions.",
        )
    ]
    assert semantic_issues("The active users are limited to 250.", evidence)


@pytest.mark.parametrize(
    "claim",
    [
        "Support up to 250 registered users accessing the VPN concurrently.",
        "Authenticate 250 registered users in parallel.",
    ],
)
def test_concurrency_after_the_registered_subject_is_still_a_changed_load(claim):
    """Reproduce actual accepted drafts whose concurrent qualifier followed the noun."""
    evidence = [
        Evidence(
            id="E-001",
            source="description",
            quote="Plan for 250 registered users and 25 simultaneous sessions.",
        )
    ]
    assert any(
        "planning_population_is_not_concurrency" in code
        for code in semantic_issues(claim, evidence)
    )


@pytest.mark.parametrize(
    "claim",
    [
        "Support up to 25 simultaneous sessions.",
        "Deny a new request beyond the 25-session limit.",
        "The maximum of 250 registered users defines the peak load.",
    ],
)
def test_supporting_a_load_does_not_define_a_rejection_cap(claim):
    """Neither an upper limit nor overload denial follows from the stated supported load."""
    evidence = [
        Evidence(
            id="E-001",
            source="description",
            quote="Plan for 250 registered users and 25 simultaneous sessions.",
        )
    ]
    assert any("unconfirmed_load_bound" in code for code in semantic_issues(claim, evidence))


def test_explicit_source_cap_and_postpositive_concurrency_remain_valid():
    """Do not reject those same claims when the stakeholder really stated them."""
    source = "Support up to 250 registered users accessing the VPN concurrently."
    assert not semantic_issues(source, [Evidence(id="E-001", source="description", quote=source)])
