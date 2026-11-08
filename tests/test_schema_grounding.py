"""Schema definitions guide generation without promoting retrieved content to instructions."""

import json
import threading
import time

import httpx
import pytest

from cybersrs.provider import GenerationError, OllamaProvider
from cybersrs.schemas import ChatResponse


def test_trusted_shape_is_in_prompt_while_source_values_stay_untrusted(
    settings, monkeypatch
) -> None:
    """Supply field meaning and preserve the role boundary around source-derived enum values."""
    marker = "UNTRUSTED_SOURCE_INSTRUCTION_TO_IGNORE"

    def post(url, **kwargs):
        payload = kwargs["json"]
        assert url.endswith("/api/generate")
        system = payload["system"]
        shape = json.loads(system.split("TRUSTED_OUTPUT_JSON_SCHEMA:\n", 1)[1])
        assert shape == ChatResponse.model_json_schema()
        assert marker not in system
        assert marker in payload["prompt"]
        assert marker in json.dumps(payload["format"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "response": ChatResponse(
                    answer="Validated local answer", sources=[]
                ).model_dump_json(),
                "done_reason": "stop",
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    result, _ = OllamaProvider(settings).generate(
        "Fixed trusted instruction",
        {"sources": [{"id": "C-001", "text": marker}]},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 5,
    )
    assert result.answer == "Validated local answer"


def test_context_budget_counts_the_schema_before_calling_ollama(settings, monkeypatch) -> None:
    """Reject over-budget input instead of relying on hidden truncation of schema or evidence."""

    def unexpected_post(*args, **kwargs):
        raise AssertionError("An over-budget request must not reach the model")

    monkeypatch.setattr(httpx, "post", unexpected_post)
    provider = OllamaProvider(settings.model_copy(update={"ollama_num_ctx": 2048}))
    with pytest.raises(GenerationError, match="context_budget_exceeded"):
        provider.generate(
            "x" * 6000,
            {},
            ChatResponse,
            threading.Event(),
            time.monotonic() + 5,
        )
