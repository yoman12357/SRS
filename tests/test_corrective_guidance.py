"""Known semantic failures receive concrete trusted instructions on bounded retries."""

import json
import threading
import time

import httpx
import pytest

from cybersrs.provider import OllamaProvider
from cybersrs.schemas import ChatResponse


def test_retry_explains_timing_error_and_retains_the_validation_gate(settings, monkeypatch) -> None:
    """A code alone previously made base Qwen repeat 'immediately' on every retry."""
    sent = []

    def post(url, **kwargs):
        sent.append(kwargs["json"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"response": json.dumps({"answer": "Observable result.", "sources": []})},
        )

    monkeypatch.setattr(httpx, "post", post)
    result, provenance = OllamaProvider(settings).generate(
        "Trusted instruction",
        {"source": "Original input"},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
        lambda _: ["FR-003:unsupported_response_time_commitment"] if len(sent) == 1 else [],
    )
    assert result.answer == "Observable result."
    assert provenance["attempts"] == 2
    assert "CORRECTIONS REQUIRED" not in sent[0]["system"]
    assert "Remove unrequested timing promises" in sent[1]["system"]
    assert json.loads(sent[1]["prompt"])["source"] == "Original input"


@pytest.mark.parametrize("feedback_field", ["previous_validation_failure", "validation_feedback"])
def test_untrusted_failure_text_is_not_promoted_into_system(
    settings, monkeypatch, feedback_field: str
) -> None:
    """Only fixed mapped remedies may be appended; arbitrary failure content stays data."""
    sent = []

    def post(url, **kwargs):
        sent.append(kwargs["json"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"response": json.dumps({"answer": "Observable result.", "sources": []})},
        )

    monkeypatch.setattr(httpx, "post", post)
    OllamaProvider(settings).generate(
        "Trusted instruction",
        {feedback_field: "unsupported_response_time_commitment PRIVATE_SOURCE_MARKER"},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
    )
    assert "Remove unrequested timing promises" in sent[0]["system"]
    assert "PRIVATE_SOURCE_MARKER" not in sent[0]["system"]
