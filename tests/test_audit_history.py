"""Private exact-request and source history is isolated, transactional and deletable."""

import base64
import copy
import json
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from cybersrs.api import create_app
from cybersrs.audit import audit_scope, record_model_event
from cybersrs.provider import RepairingOllamaProvider
from cybersrs.repository import Repository, canonical_hash
from cybersrs.schemas import ChatResponse

from .conftest import DESCRIPTION, FakeKnowledge, FakeProvider, wait_run


def test_source_revisions_hashes_isolation_and_project_deletion(settings):
    """Overwritten user inputs and removed references remain inspectable until project deletion."""
    repo = Repository(settings.data_dir)
    first = repo.create_project("First", DESCRIPTION)
    other = repo.create_project("Other", DESCRIPTION)
    repo.update_project(first["id"], description=DESCRIPTION + " Revised input.")
    reference = repo.add_document(
        first["id"], "local.txt", "Exact original reference text.", "fixture-digest"
    )
    repo.delete_document(first["id"], reference["id"])
    events = repo.list_audit(first["id"])
    assert events[0]["payload"]["description"] == DESCRIPTION
    assert events[1]["payload"]["changes"]["description"].endswith("Revised input.")
    assert events[1]["payload"]["previous"]["description"] == DESCRIPTION
    assert events[-1]["payload"]["text"] == reference["text"]
    assert all(canonical_hash(event["payload"]) == event["payload_hash"] for event in events)
    assert len(repo.list_audit(other["id"])) == 1
    run = repo.create_run(first["id"], "analyse", "fixture")
    with pytest.raises(ValueError, match="audit_run_project_mismatch"):
        repo.record_audit(other["id"], "bad_attribution", {}, run["id"])
    repo.delete_project(first["id"])
    with repo.connection() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM audit_event WHERE project_id=?", (first["id"],)
            ).fetchone()[0]
            == 0
        )
    assert len(repo.list_audit(other["id"])) == 1


def test_audit_failure_rolls_back_source_change(settings, monkeypatch):
    """A successful source mutation cannot silently omit its corresponding history record."""
    import cybersrs.repository as module

    repo = Repository(settings.data_dir)
    project = repo.create_project("Rollback", DESCRIPTION)

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic_audit_failure")

    monkeypatch.setattr(module, "_append_audit", fail)
    with pytest.raises(RuntimeError, match="synthetic_audit_failure"):
        repo.update_project(project["id"], description="Changed synthetic source input.")
    assert repo.get_project(project["id"])["description"] == DESCRIPTION
    assert len(repo.list_audit(project["id"])) == 1


def test_corrective_requests_are_recorded_before_inference_and_context_is_cleared(
    settings, monkeypatch
):
    """Record actual authors, schema, exact data and each validation outcome."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Audit inference", DESCRIPTION)
    run = repo.create_run(project["id"], "analyse", "fixture")
    sent = []

    def post(url, **kwargs):
        sent.append(copy.deepcopy(kwargs["json"]))
        requests = [e for e in repo.list_audit(project["id"]) if e["kind"] == "model_request"]
        assert len(requests) == len(sent)
        assert requests[-1]["payload"]["request"] == kwargs["json"]
        answer = (
            "accepted answer"
            if kwargs["json"]["model"] == settings.base_model_name
            else "rejected answer"
        )
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"response": ChatResponse(answer=answer, sources=[]).model_dump_json()},
        )

    monkeypatch.setattr(httpx, "post", post)
    with audit_scope(repo, project["id"], run["id"]):
        result, _ = RepairingOllamaProvider(settings).generate(
            "fixed instructions",
            {"question": "Private synthetic text"},
            ChatResponse,
            threading.Event(),
            time.monotonic() + 10,
            lambda value: [] if value.answer == "accepted answer" else ["unsupported_answer"],
        )
    assert result.answer == "accepted answer"
    events = repo.list_audit(project["id"])
    requests = [e for e in events if e["kind"] == "model_request"]
    assert len(requests) == 2
    assert [e["payload"]["request"]["model"] for e in requests] == [
        settings.model_name,
        settings.base_model_name,
    ]
    assert "TRUSTED_OUTPUT_JSON_SCHEMA" in requests[0]["payload"]["request"]["system"]
    assert (
        json.loads(requests[0]["payload"]["request"]["prompt"])["question"]
        == "Private synthetic text"
    )
    checks = [e["payload"]["accepted"] for e in events if e["kind"] == "model_validation"]
    assert checks == [False, True]
    responses = [e for e in events if e["kind"] == "model_response"]
    assert [e["payload"]["request_id"] for e in responses] == [e["id"] for e in requests]
    before = len(events)
    assert record_model_event("outside_context", {}) is None
    assert len(repo.list_audit(project["id"])) == before


def test_explicit_audit_download_retains_exports_and_ordinary_routes_do_not_include_history(
    settings, analysis, sections
):
    """Keep full snapshots and artifact bytes in the explicit private history export."""
    app = create_app(settings, FakeProvider(analysis, sections), FakeKnowledge())
    with TestClient(app) as client:
        project = client.post(
            "/api/v1/projects", json={"name": "Synthetic audit", "description": DESCRIPTION}
        ).json()
        path = f"/api/v1/projects/{project['id']}"
        first = client.post(path + "/analyse").json()
        assert wait_run(app.state.repository, first["id"])["status"] == "completed"
        second = client.post(path + "/generate").json()
        assert wait_run(app.state.repository, second["id"])["status"] == "completed"
        version = client.get(path + "/versions").json()[0]
        exported = client.get(path + f"/versions/{version['id']}/export/pdf")
        audit = client.get(path + "/audit")
        assert audit.status_code == 200 and "attachment" in audit.headers["content-disposition"]
        events = audit.json()["events"]
        assert any(e["kind"] == "workflow_input" for e in events)
        artifact = next(e["payload"] for e in events if e["kind"] == "artifact_exported")
        assert base64.b64decode(artifact["content_base64"]) == exported.content
        assert artifact["content_hash"] == version["content_hash"]
        assert "events" not in client.get(path).json()
        assert "audit" not in client.get(f"/api/v1/runs/{second['id']}").json()
        assert client.get(path + f"/versions/{version['id']}/reviews").json() == []
