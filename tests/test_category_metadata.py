"""Empty categories must explain real coverage without inventing product obligations."""

import copy
import threading
import time

import pytest

from cybersrs.category_metadata import (
    CATEGORY_METADATA_VERSION,
    canonical_category_ids,
    empty_category_metadata,
)
from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import GenerationError, generation_schema
from cybersrs.repository import Repository
from cybersrs.schemas import RequirementsSection

from .conftest import DESCRIPTION, FakeKnowledge, FakeProvider, requirement, wait_run


def test_empty_category_explanation_uses_actual_canonical_ids_only():
    """Do not turn a copied title or another source's prose into a new requirement."""
    metadata = empty_category_metadata(
        "data",
        [
            {"id": "SEC-002", "title": "UNTRUSTED_NEW_PRODUCT_RULE"},
            {"id": "SEC-002"},
            {"id": "FR-001"},
        ],
    )
    assert metadata["available_requirement_ids"] == ["FR-001", "SEC-002"]
    assert metadata["required_requirement_ids"] == ["FR-001", "SEC-002"]
    assert "UNTRUSTED_NEW_PRODUCT_RULE" not in metadata["applicability_reason"]
    assert empty_category_metadata("nonfunctional", [])["available_requirement_ids"] == []
    with pytest.raises(ValueError, match="unknown_requirement_category"):
        empty_category_metadata("invented-category", [])
    with pytest.raises(ValueError, match="canonical_requirement_ids_required"):
        empty_category_metadata("data", [{"id": ""}])


def test_native_empty_schema_binds_explanation_and_known_links_without_new_rows():
    """A nonempty canonical vocabulary must not reopen unrelated test authoring."""
    metadata = empty_category_metadata("data", [{"id": "SEC-002"}])
    schema = generation_schema(
        RequirementsSection,
        {
            "existing_requirements": [{"id": "SEC-002"}],
            "frozen_category_metadata": metadata,
        },
    )
    properties = schema["properties"]
    assert properties["applicability_reason"]["const"] == metadata["applicability_reason"]
    assert properties["related_requirement_ids"]["items"]["enum"] == ["SEC-002"]
    assert properties["related_requirement_ids"]["minItems"] == 1
    assert properties["requirements"]["maxItems"] == 0
    assert properties["related_acceptance_criteria"]["maxItems"] == 0
    assert "related_requirement_ids" in schema["required"]


def test_empty_parser_rejects_invented_scope_even_without_decoder_compliance(settings, analysis):
    """Reproduce the real E-12/malicious-device hallucination before checkpoint publication."""
    interpretation = analysis.model_copy(update={"assessments": []})

    class HallucinatingProvider:
        """Submit unrelated inapplicability prose through the actual validation callback."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Keep schema validity distinct from faithful coverage metadata."""
            assert context["frozen_category_metadata"]["available_requirement_ids"] == []
            result = schema.model_validate(
                {
                    "applicability_reason": "The system shall deny malicious devices under E-12.",
                    "requirements": [],
                }
            )
            assert validate(result) == ["empty_category_metadata_must_match_canonical_coverage"]
            raise GenerationError("synthetic_invented_metadata_rejected")

    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic metadata", DESCRIPTION)
    run = repo.create_run(project["id"], "generate", "synthetic-input")
    coordinator = Orchestrator(settings, repo, HallucinatingProvider(), FakeKnowledge())
    try:
        with pytest.raises(GenerationError, match="synthetic_invented_metadata_rejected"):
            coordinator._generate_requirement_passages(
                run["id"],
                "nonfunctional",
                {"assigned_section": "nonfunctional"},
                build_evidence(DESCRIPTION, []),
                interpretation,
                [],
                {},
                {},
                threading.Event(),
                time.monotonic() + 10,
            )
        assert (
            repo.get_run(run["id"])["checkpoints"]["_partial_nonfunctional"]["requirements"] == []
        )
    finally:
        coordinator.shutdown()


def test_metadata_upgrade_refreshes_empty_categories_and_reuses_valid_downstream(
    settings, analysis, sections
):
    """A metadata-only change must not redraft valid authored requirements or dependent views."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic metadata retry", DESCRIPTION)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    provider = FakeProvider(analysis, sections)
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    try:
        original = wait_run(repo, coordinator.start(project["id"])["id"])
        assert original["status"] == "completed", original["error"]
        old = original["checkpoints"]["_provenance"] | {"category_metadata_version": ""}
        bad = copy.deepcopy(original["checkpoints"]["nonfunctional"])
        bad["applicability_reason"] = "The system shall deny malicious devices under E-12."
        repo.update_run(original["id"], checkpoint=("nonfunctional", bad))
        repo.update_run(original["id"], status="failed", checkpoint=("_provenance", old))
        before = len(provider.calls)
        retry = wait_run(repo, coordinator.retry(original["id"])["id"])
        assert retry["status"] == "completed", retry["error"]
        assert provider.calls[before:] == ["nonfunctional", "data", "network"]
        assert "E-12" not in retry["checkpoints"]["nonfunctional"]["applicability_reason"]
        assert repo.get_run(original["id"])["checkpoints"]["nonfunctional"] == bad
        reused = {e["agent"] for e in retry["events"] if e.get("reused")}
        assert {"functional", "security", "architecture", "verification", "sdlc"} <= reused
        for section in ("functional", "security", "architecture", "verification", "sdlc"):
            assert retry["checkpoints"][section] == original["checkpoints"][section]
        latest = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        assert latest["content"]["category_metadata_version"] == CATEGORY_METADATA_VERSION
        assert repo.list_reviews(project["id"], latest["id"]) == []
    finally:
        coordinator.shutdown()


def test_category_agent_can_index_a_real_control_missing_from_initial_routing(settings, analysis):
    """An absent initial network label must not hide the existing network-access requirement."""
    source = "Students and guests may access the internet but must not access the staff network."
    row = requirement(source, "E-001") | {"id": "FR-001"}
    interpretation = analysis.model_copy(update={"assessments": []})

    class CategoryProvider:
        """Select a real category link from the complete canonical inventory."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """A constant explanation leaves classification meaningful but bounded to actual IDs."""
            assert context["existing_requirements"][0]["statement"] == source
            metadata = context["frozen_category_metadata"]
            assert metadata["required_requirement_ids"] == ["FR-001"]
            assert metadata["available_requirement_ids"] == ["FR-001"]
            candidate = schema.model_validate(
                {
                    "applicability_reason": metadata["applicability_reason"],
                    "requirements": [],
                    "related_requirement_ids": ["FR-001"],
                }
            )
            assert validate(candidate) == []
            return candidate, {"model": self.model_name, "attempts": 1}

    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic category index", source)
    run = repo.create_run(project["id"], "generate", "synthetic-input")
    coordinator = Orchestrator(settings, repo, CategoryProvider(), FakeKnowledge())
    try:
        result, provenance = coordinator._generate_requirement_passages(
            run["id"],
            "network",
            {"assigned_section": "network"},
            build_evidence(source, []),
            interpretation,
            [],
            {"functional": {"requirements": [row]}},
            {},
            threading.Event(),
            time.monotonic() + 10,
        )
        assert result["requirements"] == []
        assert result["related_requirement_ids"] == ["FR-001"]
        assert provenance["attempts"] == 1
    finally:
        coordinator.shutdown()


def test_explicit_canonical_topics_prevent_an_empty_network_or_data_index():
    """Use normative statements/dimensions rather than hallucinated explanation prose."""
    rows = [
        {
            "id": "FR-001",
            "statement": "Students may access the internet but not the staff network.",
        },
        {"id": "FR-002", "statement": "Network administrators may manually isolate devices."},
        {"id": "FR-003", "statement": "Do not automatically change firewall rules."},
        {"id": "SEC-002", "statement": "Retain policy-change audit records for 30 days."},
        {
            "id": "SEC-003",
            "statement": "Operators acknowledge alerts.",
            "title": "Network database throughput",
            "rationale": "Untrusted extra metadata.",
        },
    ]
    assert canonical_category_ids("network", rows) == ["FR-001", "FR-002", "FR-003"]
    assert canonical_category_ids("data", rows) == ["SEC-002"]
    assert empty_category_metadata("network", [], rows)["required_requirement_ids"] == [
        "FR-001",
        "FR-002",
        "FR-003",
    ]
