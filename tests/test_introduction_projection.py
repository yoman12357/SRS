"""Source facts must not become invented caps, reopened decisions or padded answers."""

import copy
import threading
import time

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.introduction_agent import generate_introduction
from cybersrs.introduction_projection import (
    INTRODUCTION_PROJECTION_VERSION,
    SOURCE_FACT_OVERVIEW,
    compose_introduction,
    introduction_projection_issues,
    validate_introduction_order,
)
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import generation_schema
from cybersrs.repository import Repository
from cybersrs.schemas import Evidence, EvidenceAssessment, NarrativeSection, SourceIntroductionPlan
from cybersrs.validation import validate_document, validate_section

from .conftest import DESCRIPTION, FakeKnowledge, FakeProvider, wait_run

SOURCE = (
    "Specify a secure remote-access VPN. "
    "Plan for 250 registered users and 25 simultaneous sessions. "
    "No continuous delivery is planned. Budget and protocol choices are undecided. "
    "Automatic firewall reconfiguration and active vulnerability scanning are out of scope."
)


def _facts(analysis):
    """Use actual source statements and explicit unknown/exclusion labels in isolated tests."""
    evidence = build_evidence(SOURCE, [])
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id=item.id,
                    kind="exclusion"
                    if item.id == "E-005"
                    else "uncertain"
                    if item.id == "E-004"
                    else "context",
                    sections=["introduction"],
                    explanation="The source states this project fact.",
                )
                for item in evidence
            ],
            "unresolved_decisions": ["Budget and protocol choices are undecided."],
        }
    )
    return evidence, interpretation


def test_exact_facts_preserve_load_exclusions_and_settled_delivery_decisions(analysis):
    """The model may organize facts but cannot add an upper cap or reopen continuous delivery."""
    evidence, interpretation = _facts(analysis)
    plan = SourceIntroductionPlan(evidence_order=[item.id for item in reversed(evidence)])
    content = compose_introduction(plan, evidence, interpretation)
    assert content["summary"] == SOURCE_FACT_OVERVIEW
    assert [item["detail"] for item in content["items"]] == [
        item.quote for item in reversed(evidence)
    ]
    assert [item["evidence_ids"][0] for item in content["items"]] == plan.evidence_order
    by_id = {item["evidence_ids"][0]: item for item in content["items"]}
    assert by_id["E-003"]["status"] == "confirmed"
    assert by_id["E-004"]["status"] == "unresolved"
    assert "exclusion" in by_id["E-005"]["title"]
    assert validate_section("introduction", content, evidence, interpretation, [], {}) == []
    assert introduction_projection_issues(content, evidence, interpretation) == []


@pytest.mark.parametrize("defect", ["duplicate", "unknown", "missing"])
def test_invalid_orders_cannot_drop_or_invent_source_facts(analysis, defect):
    """Native decoding is independent from the complete source-inventory check."""
    evidence, interpretation = _facts(analysis)
    order = [item.id for item in evidence]
    if defect == "duplicate":
        order.append(order[0])
    elif defect == "unknown":
        order[0] = "E-999"
    else:
        order.pop()
    plan = SourceIntroductionPlan(evidence_order=order)
    assert validate_introduction_order(plan, evidence)
    with pytest.raises(ValueError):
        compose_introduction(plan, evidence, interpretation)


def test_native_order_is_bound_to_the_complete_actual_inventory(analysis):
    """There is no section quota or free-form source identifier."""
    evidence, _ = _facts(analysis)
    schema = generation_schema(
        SourceIntroductionPlan,
        {
            "assigned_section": "introduction",
            "evidence": [item.model_dump() for item in evidence],
        },
    )
    order = schema["properties"]["evidence_order"]
    assert order["minItems"] == order["maxItems"] == len(evidence)
    assert order["items"]["enum"] == [item.id for item in evidence]
    assert order["uniqueItems"] is True


def test_exact_short_answer_keeps_question_context_without_padding_or_new_commitments(analysis):
    """A quoted Yes is valid source text; an invented short claim elsewhere remains invalid."""
    fact = Evidence(
        id="E-001",
        source="answer:Q-1",
        quote="Yes",
        context="Should connection logs be retained for 14 days?",
    )
    interpretation = analysis.model_copy(update={"assessments": [], "unresolved_decisions": []})
    content = compose_introduction(
        SourceIntroductionPlan(evidence_order=[fact.id]), [fact], interpretation
    )
    assert content["items"][0]["detail"] == "Yes"
    assert content["items"][0]["title"].endswith(fact.context)
    assert validate_section("introduction", content, [fact], interpretation, [], {}) == []
    assert any(
        "narrative_detail_too_short" in error
        for error in validate_section("glossary", content, [fact], interpretation, [], {})
    )
    bad = copy.deepcopy(content)
    bad["items"][0]["detail"] = "No"
    assert any(
        "fact_detail_must_match" in error
        for error in validate_section("introduction", bad, [fact], interpretation, [], {})
    )


@pytest.mark.parametrize("field", ["summary", "status"])
def test_current_quality_checks_claimed_projection_against_actual_content(complete_document, field):
    """A version tag cannot bless a new summary promise or altered fact status."""
    document = complete_document.model_copy(deep=True)
    document.introduction = NarrativeSection.model_validate(
        compose_introduction(
            SourceIntroductionPlan(evidence_order=[item.id for item in document.evidence]),
            document.evidence,
            document.analysis,
        )
    )
    document.introduction_projection_version = INTRODUCTION_PROJECTION_VERSION
    assert validate_document(document).status == "needs_review"
    if field == "summary":
        document.introduction.summary = "A newly asserted product promise is written here."
    else:
        document.introduction.items[0].status = "proposed"
    report = validate_document(document)
    assert report.status == "invalid"
    assert any(f.code == "introduction:source_projection_mismatch" for f in report.findings)


def test_agent_organizes_source_then_uses_full_narrative_validation(analysis):
    """The classifier cannot turn a missing source fact into a successful composed introduction."""
    evidence, interpretation = _facts(analysis)

    class FactProvider:
        """Exercise the actual typed plan and full composed-section callback."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Reject missing facts before returning a complete synthetic order."""
            assert schema is SourceIntroductionPlan
            assert context["evidence"] == [item.model_dump() for item in evidence]
            assert validate(schema(evidence_order=[]))
            result = schema(evidence_order=[item.id for item in evidence])
            assert validate(result) == []
            return result, {"model": "test-qwen", "attempts": 1}

    content, provenance = generate_introduction(
        FactProvider(),
        {},
        evidence,
        interpretation,
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert introduction_projection_issues(content, evidence, interpretation) == []
    assert provenance["introduction_projection_version"] == INTRODUCTION_PROJECTION_VERSION


def test_legacy_retry_refreshes_introduction_and_sdlc_only(settings, analysis, sections):
    """A source-fact overview change must not re-author valid requirements or linked views."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic introduction retry", DESCRIPTION)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    provider = FakeProvider(analysis, sections)
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    try:
        original = wait_run(repo, coordinator.start(project["id"])["id"])
        assert original["status"] == "completed", original["error"]
        old = original["checkpoints"]["_provenance"] | {"introduction_projection_version": ""}
        repo.update_run(original["id"], status="failed", checkpoint=("_provenance", old))
        before = len(provider.calls)
        retried = wait_run(repo, coordinator.retry(original["id"])["id"])
        assert retried["status"] == "completed", retried["error"]
        assert provider.calls[before:] == ["introduction", "sdlc"]
        for name in ("functional", "security", "architecture", "verification", "scenarios"):
            assert retried["checkpoints"][name] == original["checkpoints"][name]
        latest = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        assert (
            latest["content"]["introduction_projection_version"] == INTRODUCTION_PROJECTION_VERSION
        )
        assert repo.list_reviews(project["id"], latest["id"]) == []
    finally:
        coordinator.shutdown()


def test_reviewed_introduction_keeps_honest_edit_provenance(settings, analysis, sections):
    """An explicit intro edit remains unapproved and does not claim automatic projection."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic introduction edit", DESCRIPTION)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    provider = FakeProvider(analysis, sections)
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    try:
        original = wait_run(repo, coordinator.start(project["id"])["id"])
        assert original["status"] == "completed", original["error"]
        parent = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        run = coordinator.start(
            project["id"],
            "edit",
            version_id=parent["id"],
            section="introduction",
            edited_content=parent["content"]["introduction"],
            edit_actor="assistant",
        )
        edited = wait_run(repo, run["id"])
        assert edited["status"] == "completed", edited["error"]
        latest = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        assert latest["content"]["introduction_projection_version"] == ""
        assert (
            repo.get_version(project["id"], parent["id"])["content_hash"] == parent["content_hash"]
        )
        assert repo.list_reviews(project["id"], latest["id"]) == []
    finally:
        coordinator.shutdown()
