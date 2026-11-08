"""Regressions for the user's failed API-management run and constrained repairs."""

import json
import threading
import time
from pathlib import Path

import pytest
from pydantic import ValidationError, create_model

from cybersrs.acceptance_grounding import acceptance_response_issues
from cybersrs.atomic_requirements import (
    _repair_field,
    correction_guidance,
    generate_atomic_requirements,
)
from cybersrs.evidence import build_evidence
from cybersrs.source_obligations import criterion_target_issues, source_obligations

from .test_atomic_source_generation import SourceCriterionProvider
from .test_semantic_source_cases import case_analysis

CASE = json.loads(
    (Path(__file__).parent / "fixtures/api_access_case.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    "result",
    [
        "The system denies access according to the configured role.",
        "The request is denied based on the policy fixture.",
        "The system permits access for the permitted role.",
        "The system rejects access for the unpermitted role.",
    ],
)
def test_active_access_decisions_are_observed_enforcement_results(result):
    """Do not reject denies/permits while accepting only passive denied/allowed."""
    unit = source_obligations(
        build_evidence("The system should enforce role-based API access.", [])[0]
    )[0]
    criterion = {
        "given": "A controlled role and API permission fixture",
        "when": "An API client requests access",
        "then": result,
    }
    assert not criterion_target_issues(unit, criterion)


def test_numeric_response_code_is_unavailable_in_source_free_repair_schema():
    """The actual repeated 403 guess cannot be emitted by the constrained corrective format."""
    schema = create_model(
        "AccessRepair",
        then=(
            str,
            _repair_field("then", "The system should enforce role-based access.", "enforce"),
        ),
    )
    with pytest.raises(ValidationError):
        schema.model_validate({"then": "The client receives a 403 Forbidden response"})
    assert schema.model_validate({"then": "The system denies access for the unpermitted role"})
    assert schema.model_json_schema()["properties"]["then"]["maxLength"] == 200
    explicit = create_model(
        "ExplicitCodeRepair",
        then=(
            str,
            _repair_field(
                "then",
                "The system should enforce access and return code 403 for denial.",
                "enforce",
            ),
        ),
    )
    assert explicit.model_validate({"then": "The request is denied with code 403"})


def test_detection_repair_requires_recognition_and_still_rejects_an_added_response():
    """Constrained wording supplements rather than bypasses the semantic response gate."""
    source = "The system should detect repeated failed authentication and generate alerts."
    schema = create_model("DetectionRepair", then=(str, _repair_field("then", source, "detect")))
    with pytest.raises(ValidationError):
        schema.model_validate({"then": "The system triggers account lockout after five attempts"})
    valid = schema.model_validate({"then": "Repeated failed authentication is identified"})
    assert not acceptance_response_issues(source, valid.model_dump())
    extra = schema.model_validate(
        {"then": "Repeated failed authentication is detected and the account is locked"}
    )
    assert acceptance_response_issues(source, extra.model_dump()) == [
        "unconfirmed_automatic_response"
    ]
    feedback = correction_guidance(["FR-008:unconfirmed_automatic_response"])
    assert "recognition" in " ".join(feedback)
    assert "lockout" not in " ".join(feedback)


def test_complete_api_brief_keeps_detection_separate_even_when_source_also_mentions_alerts(
    analysis,
):
    """The actual compiler includes operation-specific guidance and passes complete source gates."""
    evidence, interpreted = case_analysis(CASE, analysis)

    class SourceAuthor(SourceCriterionProvider):
        """Exercise the real generation boundary without live inference in unit tests."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Check source guidance before returning the normal inert authored fixture."""
            for unit in context["source_obligations"]:
                if unit["operation"].startswith("detect "):
                    assert "being identified" in unit["test_focus"]
                if unit["operation"].startswith("enforce "):
                    assert "allowed or denied" in unit["test_focus"]
            return super().generate(system, context, schema, cancel, deadline, validate)

    previous = {}
    for name in ("functional", "nonfunctional"):
        output, provenance = generate_atomic_requirements(
            SourceAuthor(),
            name,
            evidence,
            interpreted,
            [],
            previous,
            threading.Event(),
            time.monotonic() + 10,
            max_test_repairs=0,
        )
        assert not provenance["repaired_test_keys"]
        previous[name] = output
