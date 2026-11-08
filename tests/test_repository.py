"""Transactional storage, immutable content, approval and tenant isolation checks."""

import copy

import pytest

from cybersrs.repository import Repository, canonical_hash, source_input_hash
from cybersrs.validation import validate_document


def test_versions_are_immutable_and_approval_hash_bound(tmp_path, complete_document):
    """An edit cannot inherit approval or mutate a prior canonical baseline."""
    repo = Repository(tmp_path)
    project = repo.create_project("Synthetic", complete_document.original_description)
    quality = validate_document(complete_document).model_dump()
    first = repo.save_version(project["id"], complete_document.model_dump(), quality)
    with pytest.raises(ValueError):
        repo.add_review(project["id"], first["id"], "wrong-hash", "approve", "Test", "")
    repo.add_review(
        project["id"], first["id"], first["content_hash"], "approve", "Test", "Fixture only"
    )
    revised = copy.deepcopy(first["content"])
    revised["title"] = "Revised synthetic title"
    second = repo.save_version(project["id"], revised, quality)
    assert second["sequence"] == 2 and first["content_hash"] != second["content_hash"]
    assert not repo.list_reviews(project["id"], second["id"])
    assert repo.get_version(project["id"], first["id"])["content"] == first["content"]


def test_project_isolation_cascade_and_stale_input_guard(tmp_path, complete_document):
    """A stale worker cannot save over changed input or access another project's version."""
    repo = Repository(tmp_path)
    project = repo.create_project("Synthetic", complete_document.original_description)
    other = repo.create_project("Other", "Another synthetic cybersecurity project description.")
    original_hash = canonical_hash({"description": project["description"], "answers": []})
    quality = validate_document(complete_document).model_dump()
    version = repo.save_version(
        project["id"], complete_document.model_dump(), quality, expected_input_hash=original_hash
    )
    with pytest.raises(KeyError):
        repo.get_version(other["id"], version["id"])
    run = repo.create_run(project["id"], "generate", original_hash)
    repo.update_run(run["id"], checkpoint=("intro", {"safe": True}), event={"agent": "intro"})
    assert repo.get_run(run["id"])["checkpoints"]["intro"]["safe"]
    assert repo.interrupt_stale_runs() == 1
    repo.update_project(project["id"], description="Changed authoritative project description.")
    with pytest.raises(ValueError):
        repo.save_version(
            project["id"],
            complete_document.model_dump(),
            quality,
            expected_input_hash=original_hash,
        )
    document = repo.add_document(project["id"], "ref.txt", "Reference text", "hash")
    assert repo.list_documents(project["id"])[0]["id"] == document["id"]
    with pytest.raises(KeyError):
        repo.delete_document(other["id"], document["id"])
    repo.delete_project(project["id"])
    with pytest.raises(KeyError):
        repo.get_run(run["id"])
    assert repo.get_project(other["id"])


def test_reference_revision_invalidates_stale_analysis(tmp_path):
    """A reference added during inference must not receive a stale analysis baseline."""
    repo = Repository(tmp_path)
    project = repo.create_project("Synthetic", "Specify a defensive network access policy system.")
    before = source_input_hash(project)
    document = repo.add_document(project["id"], "policy.txt", "New requirements", "hash")
    assert source_input_hash(repo.get_project(project["id"])) != before
    with pytest.raises(ValueError, match="analysis_inputs_changed"):
        repo.update_project(project["id"], analysis={"stale": True}, expected_input_hash=before)
    repo.delete_document(project["id"], document["id"])
    assert source_input_hash(repo.get_project(project["id"])) == before
