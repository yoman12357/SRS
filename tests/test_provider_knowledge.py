"""Provider repair, loopback restrictions and private retrieval isolation."""

import json
import threading
import time

import httpx
import pytest
from pydantic import ValidationError

from cybersrs.config import Settings
from cybersrs.knowledge import KnowledgeBase, chunk_text, extract_text
from cybersrs.provider import GenerationError, OllamaProvider, generation_schema
from cybersrs.schemas import ChatResponse


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.com",
        "http://192.168.1.2:11434",
        "http://user:secret@127.0.0.1:11434",
        "http://localhost/redirect",
    ],
)
def test_config_rejects_remote_or_credentialed_model(settings, url):
    """A configuration change cannot silently send project content to a remote model."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **(settings.model_dump() | {"ollama_base_url": url}))


def test_provider_repairs_schema_without_exposing_raw_output(settings, monkeypatch):
    """A malformed response retries with field feedback while preserving original input."""
    sent = []

    def post(url, **kwargs):
        sent.append(kwargs["json"])
        content = (
            {"unexpected": "private raw output"}
            if len(sent) == 1
            else {
                "answer": "A validated local cybersecurity answer.",
                "sources": [],
            }
        )
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "response": json.dumps(content),
                "done_reason": "stop",
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    result, provenance = OllamaProvider(settings).generate(
        "fixed system",
        {"question": "original evidence"},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
    )
    assert result.answer.startswith("A validated") and provenance["attempts"] == 2
    retry = json.loads(sent[1]["prompt"])
    assert retry["question"] == "original evidence" and retry["corrective_feedback"]
    assert "private raw output" not in str(retry)
    assert sent[0]["format"]["additionalProperties"] is False


def test_truncation_is_not_a_valid_completed_section(settings, monkeypatch):
    """Even syntactically complete JSON must not hide an Ollama length limit."""
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, **kwargs: httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "done_reason": "length",
                "response": '{"answer":"short partial answer","sources":[]}',
            },
        ),
    )
    with pytest.raises(GenerationError, match="section_output_truncated"):
        OllamaProvider(settings).generate(
            "fixed", {}, ChatResponse, threading.Event(), time.monotonic() + 10
        )


def test_local_private_index_never_leaks_other_projects(settings, monkeypatch):
    """Use actual Chroma storage with deterministic local embeddings, no external model calls."""
    knowledge = KnowledgeBase(settings.model_copy(update={"rag_enabled": True}))
    monkeypatch.setattr(knowledge, "_embed", lambda texts: [[1.0, 0.0, 0.0] for _ in texts])
    knowledge.ingest("doc-a", "A", "Only project A may view this private reference.", "hash-a", "A")
    knowledge.ingest("doc-b", "B", "Only project B may view this private reference.", "hash-b", "B")
    assert not knowledge.retrieve("reference")
    result = knowledge.retrieve("reference", "A")
    assert len(result) == 1 and result[0].source_document_id == "doc-a"
    assert result[0].chunk_index == 0 and result[0].page_or_section
    knowledge.delete_private("A")
    assert not knowledge.retrieve("reference", "A")
    assert len(knowledge.retrieve("reference", "B")) == 1


def test_reference_parser_and_chunk_tail():
    """Reject executable files and preserve the end of long input text."""
    with pytest.raises(ValueError):
        extract_text("payload.exe", b"not a document")
    assert extract_text("notes.md", b"local reference") == "local reference"
    chunks = chunk_text("a" * 4000 + "END")
    assert chunks[-1].endswith("END")


def test_generation_grammar_limits_literal_quotes_without_changing_canonical_schema():
    """Native generation may select only original citation text, never paraphrased quotes."""
    context = {
        "sources": [{"id": "kb:0", "text": "Access must be authorized. Deny unknown users."}]
    }
    generated = generation_schema(ChatResponse, context)
    citation = generated["$defs"]["Citation"]["anyOf"][0]["properties"]
    assert citation["chunk_id"]["const"] == "kb:0"
    assert "Access must be authorized." in citation["quote"]["enum"]
    assert (
        "enum" not in ChatResponse.model_json_schema()["$defs"]["Citation"]["properties"]["quote"]
    )
