"""Regression checks for the actual advisory scope and lifecycle inventions."""

import copy

import pytest

from cybersrs.advisory_candidates import glossary_candidates, risk_candidates, threat_candidates
from cybersrs.artifact_grounding import unsupported_delivery_guarantees
from cybersrs.evidence import build_evidence
from cybersrs.lifecycle_projection import compose_lifecycle, validate_work_groups
from cybersrs.provider import generation_schema
from cybersrs.schemas import EvidenceAssessment, LifecycleWorkPlan, RequirementsSection
from cybersrs.sdlc import MODELS
from cybersrs.source_completion import source_permission_statement
from cybersrs.validation import assign_ids, requirements_from, validate_section

from .conftest import DESCRIPTION, requirement


@pytest.mark.parametrize("model", MODELS)
def test_compiled_lifecycle_preserves_method_and_canonical_work(model, sections, analysis):
    """Check methodology structure, complete coverage and all V test-level relationships."""
    previous = {name: assign_ids(name, copy.deepcopy(value)) for name, value in sections.items()}
    rows = requirements_from(previous)
    plan = LifecycleWorkPlan(
        justification=(
            "The supplied source factors determine a provisional lifecycle choice "
            "requiring human review."
        ),
        work_groups=[{"requirement_ids": [row["id"] for row in rows]}],
    )
    evidence = build_evidence(DESCRIPTION, [])
    output = compose_lifecycle(plan, model, rows, previous["verification"], evidence, analysis)
    assert output["selected_model"] == model
    assert validate_section("sdlc", output, evidence, analysis, [], previous) == []
    assert all(row["statement"] in str(output["phases"]) for row in rows)
    assert all(test["id"] in str(output["phases"]) for test in previous["verification"]["tests"])
    assert all(phase["human_approval"].startswith("Pending") for phase in output["phases"])
    assert all(role.startswith("Proposed") for phase in output["phases"] for role in phase["roles"])
    assert (len(output["verification_pairs"]) == 4) is (model == "V-Model")


def test_lifecycle_cannot_omit_or_duplicate_a_source_work_unit():
    """A compact model response is not allowed to lose canonical obligations."""
    rows = [requirement("The system shall allow alert review.", "E-001") | {"id": "FR-001"}]
    plan = LifecycleWorkPlan(
        justification="Source facts require a human-reviewed lifecycle recommendation.",
        work_groups=[],
    )
    assert validate_work_groups(plan, rows)
    plan = LifecycleWorkPlan(
        justification=plan.justification, work_groups=[{"requirement_ids": ["FR-999"]}]
    )
    assert validate_work_groups(plan, rows)


def test_advisory_candidates_preserve_no_automation_and_expose_unknowns(analysis):
    """A proposed risk mitigation must not reopen an explicitly excluded automatic action."""
    source = (
        "Network administrators may manually isolate a device and restore its access. "
        "The system must record administrator policy changes and retain audit records for 30 days. "
        "Do not automatically change firewall rules or isolate devices. "
        "Budget and response-time thresholds are undecided."
    )
    evidence = build_evidence(source, [])
    rows = [
        requirement(fact.quote, fact.id) | {"id": f"FR-{i:03d}"}
        for i, fact in enumerate(evidence[:3], 1)
    ]
    candidates = threat_candidates(evidence, rows)
    assert {item["key"].split("/")[-1] for item in candidates} >= {
        "privileged-misuse",
        "record-loss",
        "excluded-action",
    }
    assert "Misuse" in candidates[0]["content"]["scenario"]
    assert all(item["content"]["control_requirement_ids"] for item in candidates)
    assert all("compliance" not in item["content"]["impact"] for item in candidates)
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id=evidence[-1].id,
                    kind="uncertain",
                    sections=["introduction"],
                    explanation="The source leaves project decisions open.",
                )
            ]
        }
    )
    risks = risk_candidates(
        evidence, interpretation, {"threats": [item["content"] for item in candidates]}
    )
    assert risks[0]["content"]["evidence_ids"] == [evidence[-1].id]
    assert all(
        item["content"]["likelihood"] == item["content"]["impact"] == "unknown" for item in risks
    )
    assert all(item["content"]["owner"] == "TBD" for item in risks)
    assert all("threshold" not in item["content"]["mitigation"] for item in risks)
    assert all("automated isolation" not in item["content"]["mitigation"] for item in risks)
    terms = glossary_candidates(evidence)
    assert all(item["content"]["status"] == "proposed" for item in terms)
    assert "VPN" not in {item["content"]["title"] for item in terms}


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Network administrators may manually isolate a device and restore its access.", True),
        ("Operators may review alerts but may not change policies.", True),
        ("Admins manage permissions; support operators may inspect logs.", False),
        ("Admins may manage accounts and operators may inspect logs.", False),
        ("Whether operators may change policies remains undecided.", False),
    ],
)
def test_single_role_native_permission_keeps_exact_source(source, expected):
    """Do not turn uncertain or multi-role passages into one frozen permission."""
    statement = source_permission_statement(source)
    assert (statement == source) is expected
    if expected:
        schema = generation_schema(RequirementsSection, {"source_permission_statement": statement})
        assert schema["$defs"]["Requirement"]["properties"]["statement"]["const"] == source
        assert schema["properties"]["requirements"]["maxItems"] == 1


def test_unprovided_authentication_flow_is_not_an_access_requirement():
    """A controlled role fixture remains possible without requiring a new login feature."""
    evidence = build_evidence("Students may access the internet.", [])
    assert "unconfirmed_authentication_flow" in unsupported_delivery_guarantees(
        "Process the user through the authentication flow.", evidence
    )
    assert not unsupported_delivery_guarantees(
        "Represent a student using a controlled test identity.", evidence
    )
    explicit = build_evidence("Users authenticate before accessing resources.", [])
    assert not unsupported_delivery_guarantees("Process the authentication flow.", explicit)
