"""Full isolated API workflows, sequential ordering, failure retention and cancellation."""

import copy
import threading

import pymupdf
from fastapi.testclient import TestClient

from cybersrs.api import create_app
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import check_cancel
from cybersrs.repository import Repository
from cybersrs.schemas import SECTION_SCHEMAS

from .conftest import DESCRIPTION, FakeKnowledge, FakeProvider, requirement, wait_run


def test_architecture_edit_rebuilds_threats_and_risks_from_new_design(settings, analysis, sections):
    """A design revision must replace stale threat/risk context while preserving old versions."""

    class InspectDesignProvider(FakeProvider):
        """Capture the validated design actually supplied to downstream specialists."""

        def __init__(self):
            """Keep request contexts separate from mutable fixture data."""
            super().__init__(analysis, sections)
            self.designs = []

        def generate(self, system, context, schema, cancel, deadline, validate=None):
            """Inspect dependency context before executing the ordinary fake boundary."""
            if context.get("assigned_section") in {"threats", "risks"}:
                self.designs.append(
                    (context["assigned_section"], copy.deepcopy(context["design_context"]))
                )
            return super().generate(system, context, schema, cancel, deadline, validate)

    provider = InspectDesignProvider()
    app = create_app(settings, provider, FakeKnowledge())
    with TestClient(app) as client:
        project = client.post(
            "/api/v1/projects", json={"name": "Synthetic design", "description": DESCRIPTION}
        ).json()
        base = f"/api/v1/projects/{project['id']}"
        analysed = client.post(base + "/analyse").json()
        assert wait_run(app.state.repository, analysed["id"])["status"] == "completed"
        generated = client.post(base + "/generate").json()
        assert wait_run(app.state.repository, generated["id"])["status"] == "completed"
        original = client.get(base + "/versions").json()[0]
        original_path = base + f"/versions/{original['id']}"
        version = client.get(original_path).json()
        edited = copy.deepcopy(version["content"]["architecture"])
        owner = next(
            item for item in edited["items"] if item["component_name"] == "Operations service"
        )
        owner["responsibility"] = (
            "Authorize account requests and operator alert review in the service."
        )
        provider.calls.clear()
        provider.designs.clear()
        response = client.put(
            original_path + "/sections/architecture",
            json={"content": edited, "expected_content_hash": version["content_hash"]},
        )
        assert response.status_code == 202
        run = wait_run(app.state.repository, response.json()["id"])
        assert run["status"] == "completed", run["error"]
        assert provider.calls == ["threats", "risks"]
        assert [name for name, _ in provider.designs] == ["threats", "risks"]
        assert all(
            next(
                item
                for item in design["components"]
                if item["component_name"] == "Operations service"
            )["responsibility"]
            == owner["responsibility"]
            for _, design in provider.designs
        )
        newest = client.get(base + "/versions").json()[0]
        assert newest["content_hash"] != original["content_hash"]
        revised = client.get(base + f"/versions/{newest['id']}").json()
        assert revised["content"]["architecture"] == edited
        assert client.get(original_path).json()["content_hash"] == version["content_hash"]
        assert not client.get(base + f"/versions/{newest['id']}/reviews").json()


def test_api_generation_exports_and_revision(settings, analysis, sections):
    """Create, analyse, generate, export and revise the same canonical data through HTTP."""
    provider = FakeProvider(analysis, sections)
    app = create_app(settings, provider, FakeKnowledge())
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/projects", json={"name": "Synthetic", "description": DESCRIPTION}
        )
        assert created.status_code == 201
        project_id = created.json()["id"]
        base = f"/api/v1/projects/{project_id}"
        run_id = client.post(base + "/analyse").json()["id"]
        assert wait_run(app.state.repository, run_id)["status"] == "completed"
        run_id = client.post(base + "/generate").json()["id"]
        run = wait_run(app.state.repository, run_id)
        assert run["status"] == "completed", run["error"]
        from itertools import groupby

        assert [name for name, _ in groupby(provider.calls)] == ["analysis", *SECTION_SCHEMAS]
        assert all(name in run["checkpoints"] for name in SECTION_SCHEMAS)
        version_id = client.get(base + "/versions").json()[0]["id"]
        version_path = base + f"/versions/{version_id}"
        version = client.get(version_path).json()
        assert version["quality"]["status"] == "needs_review"
        assert not client.get(version_path + "/reviews").json()
        md = client.get(version_path + "/export/markdown")
        assert md.status_code == 200 and "FR-001" in md.text and DESCRIPTION in md.text
        pdf = client.get(version_path + "/export/pdf")
        assert pdf.status_code == 200
        with pymupdf.open(stream=pdf.content, filetype="pdf") as parsed:
            text = "\n".join(page.get_text() for page in parsed)
            assert "FR-001" in text and "SEC-001" in text
            assert "Contents" in text and "Traceability" in text
            assert "IEEE 830-1998" in text and "Overall description" in text
            assert "human review required" in text
        assert version["presentation"]["profile"] == "ieee-830-1998-1.0"
        full = client.get(version_path + "/export/pdf?detail=full")
        with pymupdf.open(stream=full.content, filetype="pdf") as parsed:
            text = "\n".join(page.get_text() for page in parsed)
            assert "Requirements traceability matrix" in text
            assert "SDLC recommendation and workflow" in text
        assert client.get(version_path).json()["content_hash"] == version["content_hash"]
        edit = version["content"]["functional"]
        edit["requirements"][0]["rationale"] = (
            "Human clarified the reason for operator alert review."
        )
        response = client.put(
            version_path + "/sections/functional",
            json={
                "content": edit,
                "expected_content_hash": version["content_hash"],
            },
        )
        assert response.status_code == 202
        revised_run = wait_run(app.state.repository, response.json()["id"])
        assert revised_run["status"] == "completed", revised_run["error"]
        newest = client.get(base + "/versions").json()[0]
        assert newest["id"] != version_id
        revised = client.get(base + f"/versions/{newest['id']}").json()
        assert revised["content"]["security"] == version["content"]["security"]
        assert revised["content"]["functional"] == edit
        assert not client.get(base + f"/versions/{newest['id']}/reviews").json()
        assert client.get("/api/v1/runs/does-not-exist").status_code == 404
        assert (
            client.post(
                base + "/generate", headers={"Origin": "https://untrusted.invalid"}
            ).status_code
            == 403
        )
        assert client.delete(base).status_code == 204
        assert client.get(base).status_code == 404


def test_failure_keeps_validated_sections_without_success_version(settings, analysis, sections):
    """A failed specialist must not fabricate/fallback a completed report."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic", DESCRIPTION)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    provider = FakeProvider(analysis, sections)
    provider.fail_section = "security"
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    try:
        run = wait_run(repo, coordinator.start(project["id"])["id"])
        assert run["status"] == "failed"
        assert "functional" in run["checkpoints"] and "security" not in run["checkpoints"]
        assert not repo.list_versions(project["id"])
        provider.fail_section = None
        calls_before_retry = list(provider.calls)
        resumed = wait_run(repo, coordinator.retry(run["id"])["id"])
        assert resumed["status"] == "completed", resumed["error"]
        assert provider.calls[len(calls_before_retry) :][0] == "security"
        assert any(event.get("reused") for event in resumed["events"])
        assert len(repo.list_versions(project["id"])) == 1
    finally:
        coordinator.shutdown()


def test_sdlc_version_change_reuses_only_revalidated_predecessors(settings, analysis, sections):
    """An SDLC-only change must rebuild that section while preserving valid earlier work."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic", DESCRIPTION)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    provider = FakeProvider(analysis, sections)
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    try:
        run = wait_run(repo, coordinator.start(project["id"])["id"])
        assert run["status"] == "completed", run["error"]
        old = run["checkpoints"]["_provenance"] | {"sdlc_prompt_version": "old-test-profile"}
        # Simulate a terminated commit after checkpoint persistence in isolated storage.
        repo.update_run(run["id"], status="failed", checkpoint=("_provenance", old))
        before = len(provider.calls)
        retry = wait_run(repo, coordinator.retry(run["id"])["id"])
        assert retry["status"] == "completed", retry["error"]
        assert provider.calls[before:] == ["sdlc"]
        reused = {event["agent"] for event in retry["events"] if event.get("reused")}
        assert "verification" in reused and "architecture" in reused and "sdlc" not in reused
    finally:
        coordinator.shutdown()


def test_reviewed_failed_checkpoint_corrections_are_validated_and_attributed(
    settings, analysis, sections
):
    """A failed section can be repaired without a fake completed version or human approval."""
    provider = FakeProvider(analysis, sections)
    provider.fail_section = "architecture"
    app = create_app(settings, provider, FakeKnowledge())
    with TestClient(app) as client:
        repo = app.state.repository
        project = repo.create_project("Synthetic", DESCRIPTION)
        repo.update_project(project["id"], analysis=analysis.model_dump())
        run = wait_run(repo, app.state.coordinator.start(project["id"])["id"])
        assert run["status"] == "failed" and not repo.list_versions(project["id"])
        path = f"/api/v1/runs/{run['id']}/retry"
        payload = {
            "section_edits": {"architecture": sections["architecture"]},
            "expected_input_hash": "stale",
            "editor": "assistant",
        }
        assert client.post(path, json=payload).status_code == 409
        payload["expected_input_hash"] = run["input_hash"]
        bad = copy.deepcopy(payload)
        bad["section_edits"]["architecture"]["items"][0]["requirement_ids"] = ["FR-999"]
        response = client.post(path, json=bad)
        assert response.status_code == 202
        failed = wait_run(repo, response.json()["id"])
        assert failed["status"] == "failed" and not repo.list_versions(project["id"])
        response = client.post(path, json=payload)
        completed = wait_run(repo, response.json()["id"])
        assert completed["status"] == "completed", completed["error"]
        assert any(e.get("model") == "assistant_edit" for e in completed["events"])
        assert any(e.get("reused") for e in completed["events"])
        version = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        assert version["content"]["section_models"]["architecture"] == ["assistant_edit"]
        assert "assistant_edit" not in version["content"]["models_used"]
        assert not repo.list_reviews(project["id"], version["id"])


def test_applicability_wording_edit_preserves_validated_dependent_artifacts(
    settings, analysis, sections
):
    """Correcting explanatory text must not replace unchanged requirements and design."""
    provider = FakeProvider(analysis, sections)
    app = create_app(settings, provider, FakeKnowledge())
    with TestClient(app) as client:
        repo = app.state.repository
        project = repo.create_project("Synthetic", DESCRIPTION)
        repo.update_project(project["id"], analysis=analysis.model_dump())
        first = wait_run(repo, app.state.coordinator.start(project["id"])["id"])
        assert first["status"] == "completed", first["error"]
        version = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        content = copy.deepcopy(version["content"]["data"])
        content["applicability_reason"] = (
            "No separate data requirement is confirmed by this source."
        )
        provider.calls.clear()
        response = client.put(
            f"/api/v1/projects/{project['id']}/versions/{version['id']}/sections/data",
            json={
                "content": content,
                "editor": "assistant",
                "expected_content_hash": version["content_hash"],
            },
        )
        edited = wait_run(repo, response.json()["id"])
        assert edited["status"] == "completed", edited["error"]
        assert provider.calls == []

        revised = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        for name in ("architecture", "threats", "scenarios", "verification", "sdlc"):
            assert revised["content"][name] == version["content"][name]
        classification = copy.deepcopy(revised["content"]["functional"])
        classification["requirements"][0]["dimensions"] = ["technical", "security"]
        response = client.put(
            f"/api/v1/projects/{project['id']}/versions/{revised['id']}/sections/functional",
            json={
                "content": classification,
                "editor": "assistant",
                "expected_content_hash": revised["content_hash"],
            },
        )
        result = wait_run(repo, response.json()["id"])
        assert result["status"] == "completed", result["error"]
        assert provider.calls == []


def test_reviewed_dependencies_commit_atomically_without_new_model_drafts(
    settings, analysis, sections
):
    """A reviewed criterion repair and its reviewed views must form one validated successor."""
    provider = FakeProvider(analysis, sections)
    knowledge = FakeKnowledge()
    app = create_app(settings, provider, knowledge)
    with TestClient(app) as client:
        repo = app.state.repository
        project = repo.create_project("Synthetic", DESCRIPTION)
        repo.update_project(project["id"], analysis=analysis.model_dump())
        initial = wait_run(repo, app.state.coordinator.start(project["id"])["id"])
        assert initial["status"] == "completed", initial["error"]
        version = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        edited = copy.deepcopy(version["content"]["functional"])
        edited["requirements"][0]["acceptance_criteria"][0]["observable_evidence"] = (
            "Capture the permitted alert response and operator test identity."
        )
        dependents = {
            name: version["content"][name]
            for name in (
                "compliance",
                "architecture",
                "threats",
                "risks",
                "scenarios",
                "verification",
                "sdlc",
            )
        }
        path = f"/api/v1/projects/{project['id']}/versions/{version['id']}/sections/functional"
        payload = {
            "content": edited,
            "expected_content_hash": version["content_hash"],
            "editor": "assistant",
            "dependent_edits": dependents,
        }
        bad = copy.deepcopy(payload)
        bad["dependent_edits"]["introduction"] = version["content"]["introduction"]
        assert client.put(path, json=bad).status_code == 409
        provider.calls.clear()
        retrieval_calls = []
        original_retrieve = knowledge.retrieve

        def observe_retrieval(*args, **kwargs):
            retrieval_calls.append(args)
            return original_retrieve(*args, **kwargs)

        knowledge.retrieve = observe_retrieval
        response = client.put(path, json=payload)
        assert response.status_code == 202
        run = wait_run(repo, response.json()["id"])
        assert run["status"] == "completed", run["error"]
        assert provider.calls == []
        assert retrieval_calls == []
        assert len(repo.list_versions(project["id"])) == 2
        latest = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        assert latest["content"]["functional"] == edited
        assert latest["content"]["introduction"] == version["content"]["introduction"]
        assert not repo.list_reviews(project["id"], latest["id"])


def test_live_cancellation_discards_inflight_output(settings, analysis, sections):
    """Cancel the confirmed worker handle, then ensure no partial document commits."""
    entered = threading.Event()

    class BlockingProvider(FakeProvider):
        """Hold a real worker call until the test sends cooperative cancellation."""

        def generate(self, system, context, schema, cancel, deadline, validate=None):
            entered.set()
            while not cancel.wait(0.01):
                check_cancel(cancel, deadline)
            check_cancel(cancel, deadline)

    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic", DESCRIPTION)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    coordinator = Orchestrator(
        settings, repo, BlockingProvider(analysis, sections), FakeKnowledge()
    )
    try:
        run = coordinator.start(project["id"])
        assert entered.wait(2)
        coordinator.cancel(run["id"])
        assert wait_run(repo, run["id"])["status"] == "cancelled"
        assert not repo.list_versions(project["id"])
    finally:
        coordinator.shutdown()


def test_section_supplement_preserves_valid_requirements(settings, analysis, sections):
    """A missing behavior gets a targeted call without dropping the valid original item."""
    from cybersrs.schemas import EvidenceAssessment

    description = DESCRIPTION + " Network administrators manually isolate a selected device."
    analysis.assessments.append(
        EvidenceAssessment(
            evidence_id="E-003",
            kind="requirement",
            sections=["functional"],
            explanation="Explicit manual isolation permission",
        )
    )
    sections["scenarios"]["scenarios"][0]["requirement_ids"].append("FR-002")
    sections["architecture"]["items"][0]["requirement_ids"].append("FR-002")
    sections["architecture"]["items"][0]["evidence_ids"].append("E-003")
    sections["architecture"]["items"][0]["responsibility"] += (
        " Accept explicit administrator requests to manually isolate a device."
    )
    sections["verification"]["tests"][0]["requirement_ids"].append("FR-002")
    sections["sdlc"]["phases"][0]["requirement_ids"].append("FR-002")

    class SupplementalProvider(FakeProvider):
        """Return only the omitted behavior when the specialist requests completion."""

        def generate(self, system, context, schema, cancel, deadline, validate=None):
            if context.get("completion_instruction"):
                self.calls.append("functional-supplement")
                result = schema.model_validate(
                    {
                        "applicability_reason": "Complete explicit administrator device isolation.",
                        "requirements": [
                            requirement(
                                "The system shall allow network administrators "
                                "to manually isolate a device.",
                                "E-003",
                            )
                        ],
                    }
                )
                assert not validate(result)
                return result, {"model": self.model_name, "attempts": 1}
            return super().generate(system, context, schema, cancel, deadline, validate)

    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic", description)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    provider = SupplementalProvider(analysis, sections)
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    try:
        run = wait_run(repo, coordinator.start(project["id"])["id"])
        assert run["status"] == "completed", run["error"]
        version = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        generated = version["content"]["functional"]["requirements"]
        assert [item["id"] for item in generated] == ["FR-001", "FR-002"]
        assert generated[0]["statement"] == sections["functional"]["requirements"][0]["statement"]
        assert "functional-supplement" in provider.calls
    finally:
        coordinator.shutdown()
