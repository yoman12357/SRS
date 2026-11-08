"""Source-purpose access wording must not create a literal management-verb quota."""

import pytest

from cybersrs.semantics import missing_source_actions

PURPOSE = (
    "Design a secure Network Access Control (NAC) system for a university that manages "
    "access for students, faculty, staff, laboratory devices, and guests across wired "
    "and wireless networks."
)


@pytest.mark.parametrize(
    "verb", ["provide secure network access", "control network access", "regulate access"]
)
def test_system_access_purpose_accepts_equivalent_access_service_wording(verb):
    """The saved NAC response need not repeat 'manage' to express its access-service purpose."""
    text = (
        f"The system shall {verb} for students, faculty, staff, laboratory devices, "
        "and guests across wired and wireless networks."
    )
    assert "management" not in missing_source_actions(PURPOSE, text)


@pytest.mark.parametrize(
    "text",
    [
        "The system shall record audit logs.",
        "The system shall not provide secure network access.",
        "The system must never control network access.",
    ],
)
def test_absent_or_negated_access_behavior_remains_missing(text):
    """Mentioning an unrelated function or negating access does not satisfy the source purpose."""
    assert "management" in missing_source_actions(PURPOSE, text)


@pytest.mark.parametrize(
    "source",
    [
        "Network administrators manage access policies.",
        "Administrators may manage accounts.",
        "Network administrators shall manage remote-access permissions.",
        "Design a NAC system that manages access policies for students and guests.",
        "Design a NAC system that manages access permissions for students and guests.",
    ],
)
def test_administrator_management_is_not_replaced_by_generic_network_access(source):
    """Actor-bound management controls still require their own management outcome."""
    assert "management" in missing_source_actions(
        source, "The system shall provide secure network access to students and guests."
    )


def test_unrelated_audit_log_access_does_not_cover_network_access_management():
    """The equivalence applies to the network access service, not any phrase containing access."""
    assert "management" in missing_source_actions(
        PURPOSE, "The system shall provide audit log access to users over the campus network."
    )
