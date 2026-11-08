"""The saved PAM failure must pass without suppressing logging/source validators."""

import threading
import time

import pytest

from cybersrs.acceptance_grounding import acceptance_logging_issues, preserve_source_outcome
from cybersrs.atomic_requirements import generate_atomic_requirements
from cybersrs.evidence import build_evidence
from cybersrs.schemas import Analysis, EvidenceAssessment
from cybersrs.semantics import missing_source_actions
from cybersrs.source_obligations import source_obligations
from cybersrs.validation import validate_section

from .test_atomic_source_generation import SourceCriterionProvider

PAM_BRIEF = (
    "Design a secure university privileged access management (PAM) system that controls and "
    "monitors administrative access to critical servers, databases, network devices, and "
    "security tools. The system should require privileged users to authenticate before "
    "accessing protected resources, assign privileged access based on approved roles, and "
    "allow security administrators to grant, modify, suspend, and revoke privileged permissions. "
    "The platform should record privileged sessions, log administrative actions, detect repeated "
    "failed privileged-login attempts and unusual privilege use, and generate security alerts "
    "for suspicious activity. Administrators should be able to review active privileged sessions, "
    "terminate suspicious sessions, investigate access history, and review audit records. "
    "The system should integrate with existing university identity services, support multiple "
    "campus locations, and remain secure, reliable, scalable, and manageable."
)
RECORDING_SOURCE = (
    "The platform should record privileged sessions, log administrative actions, detect repeated "
    "failed privileged-login attempts and unusual privilege use, and generate security alerts "
    "for suspicious activity."
)


@pytest.mark.parametrize("modal", ["should", "shall", "must", "will", "can", "may"])
def test_explicit_modal_recording_is_not_an_invented_feature(modal):
    """All affirmative source modals keep the requested recording during normalization."""
    source = f"The platform {modal} record privileged sessions."
    criterion = {
        "then": "The system records the privileged session.",
        "observable_evidence": "External test capture of the resulting state",
    }
    assert acceptance_logging_issues(source, criterion) == []
    assert preserve_source_outcome(source, criterion) == criterion


def test_replay_of_the_exact_failed_pam_recording_criterion():
    """Replay the saved final correction that was falsely rejected on the local site."""
    criterion = {
        "given": "system records a privileged session",
        "when": "the system logs administrative actions",
        "then": "The system records a privileged session and logs administrative actions "
        "as captured in external test data.",
        "method": "test",
        "observable_evidence": "External test capture of the resulting response",
    }
    assert acceptance_logging_issues(RECORDING_SOURCE, criterion) == []
    assert preserve_source_outcome(RECORDING_SOURCE, criterion) == criterion
    assert "recording" in missing_source_actions(RECORDING_SOURCE, "")


def test_recording_can_follow_another_requested_operation():
    """A coordinated log verb is a duty; displaying existing records is still distinct."""
    source = "The system should collect events and log administrative actions."
    criterion = {
        "then": "The administrative action is recorded in the log.",
        "observable_evidence": "External test capture of the resulting response",
    }
    assert acceptance_logging_issues(source, criterion) == []


@pytest.mark.parametrize(
    "source",
    [
        "The system should not log administrative actions.",
        "The system must never record administrative actions.",
        "No actions should be logged.",
        "Privileged users should log into protected resources.",
        "Administrators should inspect existing audit records.",
        "The system should retain existing session logs.",
    ],
)
def test_negation_login_and_existing_records_do_not_authorize_new_event_logs(source):
    """Positive recording recognition must not disable the unrequested logging guard."""
    criterion = {
        "then": "The system logs a new administrative event.",
        "observable_evidence": "External test capture of the resulting response",
    }
    assert "unrequested_product_logging_use_test_instrumented_state_capture" in (
        acceptance_logging_issues(source, criterion)
    )


def test_pam_shared_predicates_permissions_and_recording_are_independent():
    """Keep actor, permission object and all distinct source predicates."""
    evidence = build_evidence(PAM_BRIEF, [])
    units = [u for e in evidence for u in source_obligations(e)]
    statements = {u.statement for u in units}
    for verb in ("grant", "modify", "suspend", "revoke"):
        assert (
            f"The system shall allow security administrators to {verb} privileged permissions."
            in statements
        )
    assert "The system shall record privileged sessions." in statements
    assert "The system shall log administrative actions." in statements
    assert any(u.action == "control" and "administrative access" in u.statement for u in units)
    assert any(u.action == "monitor" and "administrative access" in u.statement for u in units)
    assert not any("shall controls" in s or "grant, modify" in s for s in statements)
    assert "The system shall allow Administrators to terminate suspicious sessions." in statements


def test_pam_functional_generation_passes_complete_gates_without_a_repair():
    """The real compiler/schema/provider boundary covers PAM using an inert test author."""
    evidence = build_evidence(PAM_BRIEF, [])
    analysis = Analysis(
        title="Privileged Access Management",
        domain="Cybersecurity",
        supported=True,
        summary="University privileged-access management and monitoring.",
        stakeholders=["privileged users", "security administrators", "Administrators"],
        assessments=[
            EvidenceAssessment(
                evidence_id=e.id,
                kind="requirement",
                sections=["functional", "nonfunctional"],
                explanation="The original brief defines independent source obligations.",
            )
            for e in evidence
        ],
        questions=[],
        unresolved_decisions=[],
    )
    sections = {}
    for name in ("functional", "nonfunctional"):
        content, provenance = generate_atomic_requirements(
            SourceCriterionProvider(),
            name,
            evidence,
            analysis,
            [],
            sections,
            threading.Event(),
            time.monotonic() + 10,
            max_test_repairs=0,
        )
        sections[name] = content
        assert provenance["repaired_test_keys"] == []
        assert (
            validate_section(
                name,
                content,
                evidence,
                analysis,
                [],
                {k: v for k, v in sections.items() if k != name},
            )
            == []
        )
    expected_actions = {
        "control",
        "monitor",
        "require",
        "assign",
        "grant",
        "modify",
        "suspend",
        "revoke",
        "record",
        "log",
        "detect",
        "generate",
        "review",
        "terminate",
        "investigate",
        "integrate",
        "support",
    }
    covered = {
        unit.action
        for e in evidence
        for unit in source_obligations(e)
        if unit.section == "functional"
    }
    assert expected_actions <= covered
