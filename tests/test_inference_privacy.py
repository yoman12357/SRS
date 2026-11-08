"""Local masking preserves source fidelity while withholding recognized model inputs."""

import json
import threading
import time

import httpx
import pytest

from cybersrs.audit import audit_scope
from cybersrs.inference_privacy import InferencePrivacy
from cybersrs.knowledge import KnowledgeBase
from cybersrs.provider import OllamaProvider
from cybersrs.repository import Repository
from cybersrs.schemas import ChatResponse


@pytest.mark.parametrize("punctuation", [".", ",", ";", ")", '"', "!", ""])
def test_email_masking_handles_sentence_punctuation(punctuation):
    """The real local-model probe exposed an email missed immediately before a period."""
    original = "Contact privacy-test@example.invalid" + punctuation
    privacy = InferencePrivacy()
    masked = privacy.mask_text(original)
    assert "privacy-test@example.invalid" not in masked
    assert privacy.restore_value(masked) == original


@pytest.mark.parametrize(
    "original",
    [
        "Aadhaar: 1234 5678 9012",
        "passport number: AB1234567",
        "bank account number: 123456789012",
        "phone: 9876543210",
    ],
)
def test_labelled_identifier_values_are_masked(original):
    """Cover spaced Indian identifiers and labelled financial/contact formats."""
    privacy = InferencePrivacy()
    masked = privacy.mask_text(original)
    assert masked != original and privacy.values
    assert privacy.restore_value(masked) == original


def test_sensitive_values_roundtrip_with_classification_and_no_quantity_changes():
    """Protect known formats and explicit private values, preserving engineering facts."""
    raw = {
        "evidence": [
            "Contact alice@example.org or +1 415 555 0100.",
            "password=synthetic-dummy-value and SSN 123-45-6789.",
            "Use <private>Alice Example</private> for the contact.",
            "Support 250 users, 25 sessions and retain logs for 14 days at 10.0.0.1.",
        ]
    }
    privacy = InferencePrivacy()
    masked = privacy.mask_value(raw)
    assert privacy.restore_value(masked) == raw
    assert masked["evidence"][-1] == raw["evidence"][-1]
    for value in (
        "alice@example.org",
        "+1 415 555 0100",
        "synthetic-dummy-value",
        "123-45-6789",
        "Alice Example",
    ):
        assert value not in json.dumps(masked)
    assert set(privacy.audit_mapping()["counts"]) == {
        "email",
        "telephone",
        "credential",
        "government_identifier",
        "private_span",
    }
    assert InferencePrivacy().mask_value(raw) != masked


def test_repeated_values_and_double_digit_aliases_restore_exactly():
    """Alias 1 must not be a replacement prefix of alias 10; duplicate facts stay equal."""
    original = [f"person{i}@example.org" for i in range(12)]
    privacy = InferencePrivacy()
    masked = privacy.mask_value(original + [original[0]])
    assert masked[0] == masked[-1]
    assert privacy.restore_value(masked) == original + [original[0]]
    assert (
        privacy.restore_value("CYBERSRS_PRIVATE_unrelated_EMAIL_1__")
        == "CYBERSRS_PRIVATE_unrelated_EMAIL_1__"
    )


def test_provider_masks_wire_context_and_citations_then_validates_originals(settings, monkeypatch):
    """Native constraints and context share aliases; exact source values restore before gates."""
    original = "The contact is alice@example.org for this research project."
    sent = []

    def post(url, **kwargs):
        request = kwargs["json"]
        sent.append(request)
        assert "alice@example.org" not in json.dumps(request)
        prompt = json.loads(request["prompt"])
        text = prompt["sources"][0]["text"]
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "response": json.dumps(
                    {"answer": text, "sources": [{"chunk_id": "local:0", "quote": text}]}
                ),
                "done_reason": "stop",
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic privacy", original)
    with audit_scope(repo, project["id"]):
        result, _ = OllamaProvider(settings).generate(
            "Answer from supplied local evidence.",
            {"sources": [{"id": "local:0", "text": original}]},
            ChatResponse,
            threading.Event(),
            time.monotonic() + 5,
            lambda value: (
                []
                if value.answer == original and value.sources[0].quote == original
                else ["source_changed"]
            ),
        )
    assert result.answer == original and len(sent) == 1
    events = repo.list_audit(project["id"])
    assert any(event["kind"] == "inference_masking" for event in events)
    exact = next(
        event["payload"]["request"] for event in events if event["kind"] == "model_request"
    )
    assert exact == sent[0]


def test_embedding_inputs_are_masked(settings, monkeypatch):
    """Local embeddings must receive protected text rather than bypass the boundary."""

    def post(url, **kwargs):
        assert "alice@example.org" not in json.dumps(kwargs["json"])
        return httpx.Response(
            200, request=httpx.Request("POST", url), json={"embeddings": [[0.1, 0.2]]}
        )

    monkeypatch.setattr(httpx, "post", post)
    assert KnowledgeBase(settings)._embed(["Contact alice@example.org"]) == [[0.1, 0.2]]
