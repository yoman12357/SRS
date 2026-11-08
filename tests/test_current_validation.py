"""Current quality rules apply to stored documents and untrusted export text."""

from fastapi.testclient import TestClient

from cybersrs.api import create_app
from cybersrs.exports import _markdown_literal, document_status
from cybersrs.validation import validate_document

from .conftest import FakeKnowledge, FakeProvider


def test_old_stored_report_cannot_override_current_architecture_gate(
    settings, analysis, sections, complete_document
) -> None:
    """Read/export/review recompute quality while the exact stored content remains immutable."""
    app = create_app(settings, FakeProvider(analysis, sections), FakeKnowledge())
    repo = app.state.repository
    project = repo.create_project("Historical fixture", complete_document.original_description)
    stale_quality = validate_document(complete_document).model_dump()
    content = complete_document.model_dump()
    content["architecture"]["data_flows"] = []
    saved = repo.save_version(project["id"], content, stale_quality)
    path = f"/api/v1/projects/{project['id']}/versions/{saved['id']}"
    with TestClient(app) as client:
        current = client.get(path).json()
        assert current["quality"]["status"] == "invalid"
        assert current["content_hash"] == saved["content_hash"]
        assert client.get(path + "/export/json").json()["quality"]["status"] == "invalid"
        response = client.post(
            path + "/reviews",
            json={
                "content_hash": saved["content_hash"],
                "decision": "approve",
                "reviewer": "Synthetic fixture reviewer",
                "comment": "This test must be rejected",
            },
        )
        assert response.status_code == 409
        assert repo.list_reviews(project["id"], saved["id"]) == []
        assert repo.get_version(project["id"], saved["id"])["quality"] == stale_quality


def test_markdown_literal_cannot_embed_remote_media_or_html() -> None:
    """Model/source text is quoted literally inside the deterministic Markdown structure."""
    escaped = _markdown_literal(
        "# Forged heading\n![remote](https://example.test/a)\n<script>x</script>"
    )
    assert escaped.startswith(r"\# Forged")
    assert r"!\[remote\]" in escaped
    assert r"\<script\>" in escaped


def test_export_approval_requires_current_hash_and_current_quality() -> None:
    """Renderer callers cannot reuse an approval supplied for another content hash."""
    version = {"content_hash": "current", "quality": {"status": "needs_review"}}
    decision = {"decision": "approve", "content_hash": "old"}
    assert "DRAFT" in document_status(version, [decision])
    decision["content_hash"] = "current"
    assert document_status(version, [decision]) == "HUMAN-APPROVED BASELINE"
    version["quality"]["status"] = "invalid"
    assert "INVALID DRAFT" in document_status(version, [decision])
