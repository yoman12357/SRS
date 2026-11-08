"""Repair source load scope before asking for tests of an invented capacity ceiling."""

import copy
import threading
import time

import pytest

from cybersrs.artifact_grounding import unsupported_delivery_guarantees
from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import GenerationError, generation_schema
from cybersrs.repository import Repository
from cybersrs.requirement_repair import normative_header_issues, repair_source_capacity_criterion
from cybersrs.schemas import AcceptanceTestRepair, EvidenceAssessment, ObservableEvidenceRepair
from cybersrs.semantics import missing_source_quantities
from cybersrs.source_completion import capacity_repair_statement

from .conftest import FakeKnowledge, requirement
from .test_permission_verification import criterion


@pytest.mark.parametrize(
    "source,claim",
    [
        ("25 simultaneous sessions", "25 concurrent active remote-access connections"),
        ("25 concurrent users", "25 simultaneous users"),
    ],
)
def test_concurrency_aliases_do_not_create_an_extra_missing_requirement(source, claim):
    """A quantity already present under an equivalent execution-load term is not omitted."""
    assert missing_source_quantities(source, claim) == set()
    assert missing_source_quantities("250 registered users", "25 concurrent users") == set()
    assert missing_source_quantities("25 simultaneous sessions", "250 registered users")


@pytest.mark.parametrize(
    "source,text,rejected",
    [
        ("Plan for 25 simultaneous sessions.", "This establishes an upper bound.", True),
        ("Support at most 25 simultaneous sessions.", "This establishes an upper bound.", False),
        ("Plan for 25 simultaneous sessions.", "The upper bound remains unknown.", False),
        ("Plan for 25 simultaneous sessions.", "No capacity ceiling is specified.", False),
        (
            "Plan for 25 simultaneous sessions.",
            "This does not introduce an upper bound, maximum capacity, or performance threshold.",
            False,
        ),
        (
            "Plan for 25 simultaneous sessions.",
            "No maximum capacity is specified; impose a hard capacity limit.",
            True,
        ),
    ],
)
def test_qualitative_bounds_need_actual_source_support(source, text, rejected):
    """An invented bound is still an added claim when its rationale omits the number."""
    issues = unsupported_delivery_guarantees(text, build_evidence(source, []))
    assert ("unconfirmed_capacity_ceiling" in issues) is rejected


def test_invalid_capacity_header_gets_fresh_row_repair_before_criterion_repair(settings, analysis):
    """Do not author a denial test against the original model's unsupported maximum."""
    source = "The system must support 25 simultaneous sessions."
    evidence = build_evidence(source, [])
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["functional"],
                    explanation="The stakeholder states a simultaneous execution load.",
                )
            ]
        }
    )
    row = requirement("The system shall support a maximum of 25 concurrent sessions.", "E-001")
    row["rationale"] = "The number is the upper bound for active connections."
    row["acceptance_criteria"] = [
        criterion(
            "25 sessions are active",
            "A 26th session is requested",
            "The extra session is denied with an error message",
        )
    ]
    original = copy.deepcopy(row)
    good = row | {
        "title": "Source-stated simultaneous load",
        "statement": "The system shall support 25 simultaneous sessions.",
        "rationale": "The source states this execution load without an upper bound.",
        "acceptance_criteria": [
            criterion(
                "A controlled test environment has 25 test sessions available",
                "Initiate 25 simultaneous sessions",
                "All 25 sessions are established concurrently",
            )
        ],
    }
    assert normative_header_issues("functional", row, evidence, interpretation, [], {})
    assert not normative_header_issues(
        "functional",
        good,
        evidence,
        interpretation,
        [],
        {"functional": {"requirements": [good]}},
    )

    class Provider:
        """Fail if criterion-only repair is attempted before correcting invalid scope."""

        model_name = "test-qwen"

        def __init__(self):
            self.calls = 0

        def generate(self, system, context, schema, cancel, deadline, validate):
            self.calls += 1
            assert schema is AcceptanceTestRepair and self.calls == 1
            assert context["task"] == "one_source_capacity_acceptance_criterion"
            assert "rejected_requirement" not in context
            assert context["source_capacity_statement"] == good["statement"]
            assert "OLD_SECTION" not in str(context) + system
            assert context["evidence"][0]["quote"] == source
            candidate = schema.model_validate(
                {
                    "requirement_id": row["id"],
                    "acceptance_criterion": good["acceptance_criteria"][0],
                }
            )
            assert validate(candidate) == []
            return candidate, {"model": self.model_name, "attempts": 1}

    provider = Provider()
    coordinator = Orchestrator(settings, Repository(settings.data_dir), provider, FakeKnowledge())
    try:
        repaired, metadata = coordinator._repair_rejected_requirements(
            "functional",
            {"applicability_reason": "The source states an execution load.", "requirements": [row]},
            {"drafting_instruction": "OLD_SECTION return every requirement"},
            evidence,
            interpretation,
            [],
            {},
            threading.Event(),
            time.monotonic() + 10,
            "original-model",
        )
        result = repaired.requirements[0].model_dump()
        assert result["statement"] == good["statement"]
        assert result["acceptance_criteria"] == good["acceptance_criteria"]
        assert result["rationale"] == "Source-stated constraint: " + source
        assert metadata["attempts"] == 1 and provider.calls == 1
        assert row == original
    finally:
        coordinator.shutdown()


@pytest.mark.parametrize(
    "source,rejected,expected",
    [
        (
            "Plan for 250 registered users and 25 simultaneous sessions.",
            "Support a maximum of 250 registered users.",
            "The system shall support a planned inventory of 250 registered users.",
        ),
        (
            "Plan for 250 registered users and 25 simultaneous sessions.",
            "Support a maximum of 25 concurrent active remote access connections.",
            "The system shall support 25 simultaneous sessions.",
        ),
        ("Plan for at most 250 registered users.", "Support 250 registered users.", None),
        ("Whether 250 registered users are needed is unknown.", "Support 250 users.", None),
        ("250 users and 25 sessions.", "Support 250 users and 25 sessions.", None),
    ],
)
def test_rejected_quantity_only_locates_original_capacity_scope(source, rejected, expected):
    """Source facts determine the statement; rejected bounds and implementation do not."""
    assert capacity_repair_statement(source, rejected) == expected


def test_planning_inventory_repair_inspects_source_population_without_registration_feature():
    """The actual mixed inventory/load source must produce distinct verification duties."""
    source = "Plan for 250 registered users and 25 simultaneous sessions."
    statement = "The system shall support a planned inventory of 250 registered users."
    row = requirement("The system shall support a maximum of 250 registered users.", "E-001")
    good = criterion(
        "The proposed design and configuration describe the planning population",
        "Inspect the planned inventory representation for 250 registered users",
        "The design and configuration account for 250 registered users",
    ) | {"method": "inspection"}

    class Provider:
        """Exercise independent method, subject and quantity gates before a valid inspection."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            native = generation_schema(schema, context)
            assert (
                native["$defs"]["AcceptanceCriterion"]["properties"]["method"]["const"]
                == "inspection"
            )

            def candidate(ac):
                return schema.model_validate(
                    {"requirement_id": row["id"], "acceptance_criterion": ac}
                )

            assert "capacity_repair_must_preserve_source_test_method" in validate(
                candidate(good | {"method": "test"})
            )
            assert "planning_inventory_does_not_require_registration_workflow" in validate(
                candidate(good | {"when": "Perform user registration for 250 users"})
            )
            assert "capacity_test_contains_other_row_quantity" in validate(
                candidate(good | {"then": "250 users sustain 25 simultaneous sessions"})
            )
            result = candidate(good)
            assert validate(result) == []
            return result, {"model": "test-qwen", "attempts": 1}

    result, _ = repair_source_capacity_criterion(
        Provider(),
        row,
        statement,
        build_evidence(source, []),
        threading.Event(),
        time.monotonic() + 5,
        lambda candidate: [],
    )
    assert result["statement"] == statement
    assert result["acceptance_criteria"] == [good]
    assert result["evidence_ids"] == row["evidence_ids"]


@pytest.mark.parametrize("bad_scope", [False, True])
def test_capacity_witness_only_repair_preserves_valid_behavior_and_cannot_hide_other_errors(
    bad_scope,
):
    """Recover the actual copied-source witness only when no other field is rejected."""
    source = "Plan for 250 registered users."
    statement = "The system shall support a planned inventory of 250 registered users."
    row = requirement(statement, "E-001")
    authored = criterion(
        "The design configuration is available",
        "Inspect the planned population of 250 registered users",
        "The configuration accounts for 250 registered users",
    ) | {
        "method": "inspection",
        "observable_evidence": "Export E-001: 'Plan for 250 registered users.'",
    }
    if bad_scope:
        authored["then"] = "The system guarantees uninterrupted service performance for 250 users"
    replacement = "Capture the reviewed configuration artifact showing 250 planned users."

    class Provider:
        """Supply an actual-schema rejected criterion, then only the missing evidence field."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            if schema is AcceptanceTestRepair:
                result = schema(requirement_id=row["id"], acceptance_criterion=authored)
                assert "capacity_witness_must_record_observed_result" in validate(result)
                raise GenerationError(
                    "section_validation_failed:copied_source_witness",
                    rejected_candidate=result.model_dump(),
                    rejected_model="test-qwen",
                    attempts=2,
                )
            assert schema is ObservableEvidenceRepair and not bad_scope
            assert context["criterion_context"] == {
                k: authored[k] for k in ("given", "when", "then", "method")
            }
            result = schema(observable_evidence=replacement)
            assert validate(result) == []
            return result, {"model": "test-qwen", "attempts": 1}

    args = (
        Provider(),
        row,
        statement,
        build_evidence(source, []),
        threading.Event(),
        time.monotonic() + 5,
        lambda candidate: [],
    )
    if bad_scope:
        with pytest.raises(GenerationError, match="copied_source_witness"):
            repair_source_capacity_criterion(*args)
    else:
        result, metadata = repair_source_capacity_criterion(*args)
        assert result["acceptance_criteria"] == [authored | {"observable_evidence": replacement}]
        assert metadata["attempts"] == 3 and metadata["capacity_witness_field_repair"]
