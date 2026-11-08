"""Monitoring product names must not impose a redundant literal monitoring verb."""

import pytest

from cybersrs.semantics import missing_source_actions

SOC_PURPOSE = (
    "Design a secure Security Operations Center (SOC) monitoring and incident-response "
    "platform for a university that collects security events from firewalls, servers, "
    "endpoints, authentication systems, and network devices."
)


@pytest.mark.parametrize("action", ["collect", "ingest", "receive"])
def test_event_collection_covers_monitoring_product_purpose(action: str) -> None:
    """The source's actual event-collection behavior covers its monitoring product name."""
    statement = (
        f"The system shall {action} security events from firewalls, servers, endpoints, "
        "authentication systems, and network devices."
    )
    assert not missing_source_actions(SOC_PURPOSE, statement, include_capabilities=True)


@pytest.mark.parametrize(
    "statement",
    [
        "The system shall store investigation notes.",
        "The system shall not collect security events.",
        "The system must never ingest security events.",
        "The system cannot receive security events.",
        "The system shall collect registration events.",
        "The system shall display a dashboard.",
    ],
)
def test_missing_negated_or_unrelated_collection_is_not_coverage(statement: str) -> None:
    """The purpose exception still requires an affirmative security-event collection outcome."""
    assert "monitoring" in missing_source_actions(SOC_PURPOSE, statement, include_capabilities=True)


@pytest.mark.parametrize(
    "source",
    [
        "The platform shall monitor authentication attempts.",
        "Design a monitoring platform that collects security events and monitors active sessions.",
        "Design a monitoring system that monitors authentication attempts.",
        "Provide security monitoring and collect security events.",
        "Design a monitoring platform that displays investigation notes.",
    ],
)
def test_explicit_monitoring_duties_cannot_be_replaced_by_collection(source: str) -> None:
    """Keep actual monitoring duties and unsupported purpose substitutions rejected."""
    assert "monitoring" in missing_source_actions(
        source, "The system shall collect security events.", include_capabilities=True
    )


@pytest.mark.parametrize("device", ["endpoints", "devices", "servers"])
def test_managed_devices_in_monitoring_purpose_are_not_a_management_action(device: str) -> None:
    """Device scope plus system-event collection must not demand an invented management feature."""
    source = (
        f"Design a secure monitoring platform for university servers and managed {device} "
        "that collects system events, authentication activity, process information, "
        "and security alerts from multiple departments."
    )
    statement = (
        "The system shall collect system events, authentication activity, process information, "
        "and security alerts from multiple departments."
    )
    assert not missing_source_actions(source, statement, include_capabilities=True)


@pytest.mark.parametrize(
    "statement",
    ["The system shall display alerts.", "The system shall not collect system events."],
)
def test_endpoint_purpose_still_requires_actual_collection(statement: str) -> None:
    """An adjective exception cannot excuse an absent or negated collection obligation."""
    source = "Design a monitoring platform for managed endpoints that collects system events."
    assert "monitoring" in missing_source_actions(source, statement, include_capabilities=True)


def test_explicit_endpoint_management_is_still_required() -> None:
    """Real manage actions in the body are distinct from the managed-device qualifier."""
    source = (
        "Design a monitoring platform for managed endpoints that collects system events "
        "and manages endpoint permissions."
    )
    assert "management" in missing_source_actions(
        source, "The system shall collect system events.", include_capabilities=True
    )
