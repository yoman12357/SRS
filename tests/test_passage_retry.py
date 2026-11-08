"""Successive failed retries must retain previously validated source passages."""

import threading
import time

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import GenerationError
from cybersrs.repository import Repository
from cybersrs.schemas import EvidenceAssessment

from .conftest import DESCRIPTION, FakeKnowledge, FakeProvider, requirement


def test_partial_siblings_survive_two_failed_passage_attempts(settings, analysis, sections) -> None:
    """Copy inherited partial checkpoints before entering the next failing model call."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic retry", DESCRIPTION)
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id=f"E-{index:03d}",
                    kind="requirement",
                    sections=["security"],
                    explanation="This source passage belongs to the security specialist.",
                )
                for index in (1, 2)
            ]
        }
    )
    provider = FakeProvider(interpretation, sections)
    provider.fail_section = "security"
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    row = requirement("The system shall allow security operators to review alerts.", "E-001")
    row["id"] = "SEC-001"
    checkpoints = {
        "_partial_security": {
            "applicability_reason": "Operator review is already validated.",
            "requirements": [row],
        }
    }
    try:
        for _ in range(2):
            run = repo.create_run(project["id"], "generate", "synthetic-input-hash")
            with pytest.raises(GenerationError, match="synthetic_model_failure"):
                coordinator._generate_requirement_passages(
                    run["id"],
                    "security",
                    {"assigned_section": "security"},
                    build_evidence(DESCRIPTION, []),
                    interpretation,
                    [],
                    {},
                    checkpoints,
                    threading.Event(),
                    time.monotonic() + 5,
                )
            checkpoints = repo.get_run(run["id"])["checkpoints"]
            assert checkpoints["_partial_security"]["requirements"] == [row]
        assert provider.calls == ["security", "security"]
    finally:
        coordinator.shutdown()
