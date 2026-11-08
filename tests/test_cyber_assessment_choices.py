"""Offline regressions for complete hypotheses and evidence-based lifecycle choices."""

import threading
import time

import pytest

from cybersrs.advisory_agent import generate_risks, generate_threats
from cybersrs.advisory_candidates import risk_candidates, threat_candidates
from cybersrs.evidence import build_evidence
from cybersrs.schemas import Analysis, SourceCandidatePlan
from cybersrs.sdlc import POLICY_VERSION, rank_sdlc
from cybersrs.validation import requirements_from


@pytest.mark.parametrize(
    "source,expected",
    [
        (
            "Campus Wi-Fi should use centralized authentication and role-based access control. "
            "Admins revoke access, monitor sessions and inspect audit logs across buildings.",
            {"account-takeover", "privilege-escalation", "stale-access", "audit-evidence-loss"},
        ),
        (
            "An email gateway should filter phishing and malicious attachments. Authorized admins "
            "release quarantined messages. Integrate with the university identity system "
            "and log actions.",
            {
                "filter-bypass",
                "malicious-admin-change",
                "compromised-integration",
                "audit-evidence-loss",
            },
        ),
        (
            "Collect authentication events from servers and endpoints across multiple departments. "
            "Detect suspicious processes, generate alerts and allow admins to isolate endpoints.",
            {
                "account-takeover",
                "compromised-integration",
                "detection-evasion",
                "malicious-admin-change",
            },
        ),
        (
            "Authorized admins create and revoke firewall rules between network segments. "
            "Monitor traffic and record policy changes across multiple campus buildings.",
            {
                "privilege-escalation",
                "malicious-admin-change",
                "audit-evidence-loss",
                "detection-evasion",
            },
        ),
    ],
)
def test_cyber_capabilities_produce_applicable_hypotheses_and_linked_risks(source, expected):
    """Ordinary should-style briefs cannot yield empty assessments or guessed ratings."""
    evidence = build_evidence(source, [])
    rows = [{"id": f"FR-{i:03d}", "evidence_ids": [e.id]} for i, e in enumerate(evidence, 1)]
    candidates = threat_candidates(evidence, rows)
    keys = {c["key"].split("/")[-1] for c in candidates}
    assert expected <= keys
    assert len(candidates) == len({c["key"] for c in candidates})
    known = {e.id for e in evidence}
    for candidate in candidates:
        assert set(candidate["content"]["evidence_ids"]) <= known
        assert candidate["content"]["control_requirement_ids"]
        assert candidate["content"]["sources"] == []
    analysis = Analysis(
        title="Test project",
        domain="Cybersecurity",
        supported=True,
        summary="Source-scoped security planning.",
        stakeholders=[],
        assessments=[],
        questions=[],
        unresolved_decisions=[],
    )
    risks = risk_candidates(evidence, analysis, {"threats": [c["content"] for c in candidates]})
    assert len(risks) == len(candidates)
    assert all(r["content"]["likelihood"] == r["content"]["impact"] == "unknown" for r in risks)
    assert all(r["content"]["owner"] == "TBD" for r in risks)


def test_excluded_capabilities_are_not_positive_hypothesis_evidence():
    """A generic fallback preserves assessment without inventing auth or integrations."""
    evidence = build_evidence(
        "No authentication is required. No integration is planned. Display a status summary.", []
    )
    candidates = threat_candidates(evidence, [{"id": "FR-001", "evidence_ids": [evidence[-1].id]}])
    assert [c["key"] for c in candidates] == ["derived/service-integrity"]
    assert "authenticated" not in str(candidates)
    assert threat_candidates(evidence, []) == []
    # Even when a prohibition has a canonical obligation, it is not a positive capability.
    all_rows = [{"id": f"FR-{i}", "evidence_ids": [e.id]} for i, e in enumerate(evidence)]
    assert not any(
        "account-takeover" in c["key"] or "compromised-integration" in c["key"]
        for c in threat_candidates(evidence, all_rows)
    )


@pytest.mark.parametrize("empty", [False, True])
def test_model_order_cannot_remove_material_threats_or_risks(sections, analysis, empty):
    """Keep complete inventories even if a compact response only orders one candidate."""
    evidence = build_evidence(
        "Security operators review alerts. Only administrators can manage accounts.", []
    )
    predecessors = {"functional": sections["functional"], "security": sections["security"]}
    # Assign final IDs before advisory specialists consume the source obligations.
    from cybersrs.validation import assign_ids

    predecessors = {name: assign_ids(name, value) for name, value in predecessors.items()}

    class OrderingProvider:
        """Mock local selections while exercising the real composition and validation."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Return a short ordering, never invoke a live model."""
            plan = SourceCandidatePlan(
                candidate_keys=[] if empty else [context["candidate_inventory"][-1]["key"]]
            )
            assert validate(plan) == []
            return plan, {"model": "offline-test", "attempts": 1}

    threats, provenance = generate_threats(
        OrderingProvider(),
        {},
        evidence,
        analysis,
        [],
        predecessors,
        threading.Event(),
        time.monotonic() + 5,
    )
    expected = threat_candidates(evidence, requirements_from(predecessors))
    assert len(threats["threats"]) == len(expected) > 1
    assert len(provenance["retained_source_candidates"]) == len(expected)
    predecessors["threats"] = threats
    risks, _ = generate_risks(
        OrderingProvider(),
        {},
        evidence,
        analysis,
        [],
        predecessors,
        threading.Event(),
        time.monotonic() + 5,
    )
    assert len(risks["risks"]) == len(threats["threats"])


@pytest.mark.parametrize(
    "text",
    [
        "Use centralized authentication and role-based access control, monitoring and audit logs.",
        "Inspect email, filter phishing, quarantine messages and monitor alerts.",
        "Collect system events from endpoints across multiple departments "
        "and detect suspicious activity.",
        "Manage firewall policies and monitor traffic across multiple campus buildings.",
    ],
)
def test_ordinary_cyber_briefs_have_differentiated_provisional_sdlc(text):
    """Derived suitability is useful while delivery facts still remain unconfirmed."""
    evidence = build_evidence(text, [])
    result = rank_sdlc(evidence)
    assert result["policy_version"] == POLICY_VERSION
    assert result["provisional"]
    assert len({c["score"] for c in result["ranked_candidates"]}) > 1
    assert result["ranked_candidates"][0]["reasons"] != ["No differentiating input evidence"]
    assert {"delivery", "budget", "schedule", "regulation", "stability"} <= set(
        result["unknown_factors"]
    )
    assert all(f["basis"] == "derived" and f["rationale"] for f in result["factors"])
    assert all(set(f["evidence_ids"]) <= {e.id for e in evidence} for f in result["factors"])


def test_sensitive_research_and_explicit_verification_have_distinct_lifecycle_rationales():
    """Risk-led and verification-led briefs must not collapse to one default method."""
    research = rank_sdlc(
        build_evidence(
            "Protect research data using access control and monitor alerts.",
            [],
        )
    )
    formal = rank_sdlc(
        build_evidence(
            "Use access control and monitor alerts. The project requires formal verification.", []
        )
    )
    assert research["required_model"] == "Spiral"
    assert formal["required_model"] == "V-Model"
    assert any(f["basis"] == "explicit" for f in formal["factors"])
    assert not formal["provisional"]
