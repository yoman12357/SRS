"""A one-row completion must not inherit instructions for an entire requirement section."""

import threading
import time

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.requirement_repair import complete_source_gaps
from cybersrs.schemas import EvidenceAssessment, Requirement
from cybersrs.semantics import missing_source_quantities
from cybersrs.source_completion import capacity_completion_statement

from .conftest import requirement
from .test_permission_verification import criterion


@pytest.mark.parametrize(
    "source,expected",
    [
        (
            "Plan for 250 registered users and 25 simultaneous sessions.",
            "The system shall support 25 simultaneous sessions.",
        ),
        ("Support at most 25 simultaneous sessions.", None),
        ("Support at least 25 simultaneous sessions.", None),
        ("Support 25 simultaneous sessions as a minimum.", None),
        ("Whether 25 simultaneous sessions are needed is undecided.", None),
        ("Plan for 250 registered users.", None),
    ],
)
def test_only_unqualified_source_execution_load_gets_a_fixed_statement(source, expected):
    """Preserve explicit bounds, uncertainty and registered-population scope without guessing."""
    metrics = missing_source_quantities(source, "")
    assert capacity_completion_statement(source, metrics) == expected


def test_single_capacity_completion_uses_clean_context_and_keeps_exact_project_constraints(
    analysis,
):
    """Reproduce bulk-context contamination without accepting a max25 rewrite or stale field."""
    source = "Plan for 250 registered users and 25 simultaneous sessions."
    unknown = "Budget and response-time thresholds are undecided."
    exclusion = "Do not automatically change firewall rules."
    evidence = build_evidence(" ".join([source, unknown, exclusion]), [])
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="constraint",
                    sections=["nonfunctional"],
                    explanation="The source states inventory and simultaneous session load.",
                ),
                EvidenceAssessment(
                    evidence_id="E-002",
                    kind="uncertain",
                    sections=["introduction"],
                    explanation="These project decisions are explicitly undecided.",
                ),
                EvidenceAssessment(
                    evidence_id="E-003",
                    kind="exclusion",
                    sections=["security"],
                    explanation="Automatic firewall changes are excluded.",
                ),
            ]
        }
    )
    existing = requirement("The system shall support 250 registered users.", "E-001")
    existing["id"] = "NFR-001"
    expected = "The system shall support 25 simultaneous sessions."
    added = requirement(expected, "E-001")
    added["dimensions"] = ["performance"]
    added["acceptance_criteria"] = [
        criterion(
            "A controlled remote-access test environment is available",
            "Initiate 25 simultaneous test sessions",
            "All 25 sessions are established and observable in the test state",
        )
    ]
    seen = []

    class Provider:
        """Produce one actual-schema row through independent source and capacity validation."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """A native constant supplements rather than replaces the full application gate."""
            seen.append(context)
            assert schema is Requirement
            assert context["task"] == "one_missing_source_requirement"
            assert not (
                {
                    "drafting_instruction",
                    "completion_instruction",
                    "acceptance_obligations",
                    "related_acceptance_requirement_ids",
                    "management_scope_instruction",
                }
                & context.keys()
            )
            assert context["scope_constraints"] == [exclusion]
            assert context["unresolved_project_decisions"] == [unknown]
            assert context["evidence"] == [evidence[0].model_dump()]
            assert (
                generation_schema(schema, context)["properties"]["statement"]["const"] == expected
            )
            assert "OLD_SECTION" not in system and "OLD_SECTION" not in str(context)
            bad = schema.model_validate(
                added
                | {"statement": "The system shall support a maximum of 25 simultaneous sessions."}
            )
            errors = validate(bad)
            assert any("unconfirmed_load_bound" in code for code in errors)
            assert "completion_must_preserve_source_statement" in errors
            candidate = schema.model_validate(added)
            assert validate(candidate) == []
            return candidate, {"model": self.model_name, "attempts": 1}

    output, models, attempts = complete_source_gaps(
        Provider(),
        "nonfunctional",
        {"requirements": [existing]},
        {
            "drafting_instruction": "OLD_SECTION return the whole category",
            "completion_instruction": "Return an array",
            "acceptance_obligations": {"actor": "unrelated"},
            "related_acceptance_requirement_ids": ["FR-999"],
            "management_scope_instruction": "WRONG_SUBTASK",
            "scope_constraints": ["STALE"],
        },
        evidence,
        interpretation,
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
        repair_tests=False,
    )
    assert len(seen) == 1 and attempts == 1 and models == {"test-qwen"}
    assert output["requirements"][0] == existing
    assert output["requirements"][1]["id"] == "NFR-002"
    assert output["requirements"][1]["statement"] == expected
