"""Bounded sensitive-value pseudonymization before local model submission."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any
from uuid import uuid4

PRIVACY_POLICY_VERSION = "local-inference-masking-1.0"
PATTERNS = [
    ("private_span", re.compile(r"<private>[\s\S]+?</private>", re.I), 0),
    (
        "credential",
        re.compile(
            r"\b(?:api[_ -]?key|access[_ -]?token|secret|password)\s*=\s*['\"]?([^\s'\"]{8,})", re.I
        ),
        1,
    ),
    ("credential", re.compile(r"\bBearer\s+([A-Za-z0-9._~+/-]{16,})", re.I), 1),
    (
        "email",
        re.compile(
            r"(?<![\w.+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}(?![\w-]|\.[A-Za-z0-9])"
        ),
        0,
    ),
    ("telephone", re.compile(r"(?<!\w)\+\d[\d ()-]{7,}\d(?!\d)"), 0),
    (
        "telephone",
        re.compile(r"\b(?:phone|telephone|mobile)(?: number)?\s*[:=]\s*(\d[\d ()-]{6,}\d)", re.I),
        1,
    ),
    ("government_identifier", re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"), 0),
    (
        "government_identifier",
        re.compile(r"\baadhaar\s*[:=]\s*(\d{4}[ -]?\d{4}[ -]?\d{4})(?!\d)", re.I),
        1,
    ),
    (
        "government_identifier",
        re.compile(r"\b(?:aadhaar|passport(?: number)?)\s*[:=]\s*([A-Z0-9][A-Z0-9-]{5,19})", re.I),
        1,
    ),
    (
        "financial_identifier",
        re.compile(r"\b(?:bank account|card)(?: number)?\s*[:=]\s*(\d[\d -]{6,23}\d)", re.I),
        1,
    ),
]


class InferencePrivacy:
    """Keep one call's opaque aliases and reversible originals in local memory."""

    def __init__(self) -> None:
        """Use a fresh unpredictable namespace to prevent source-authored alias forgery."""
        self.prefix = "CYBERSRS_PRIVATE_" + uuid4().hex
        self.values: dict[str, tuple[str, str]] = {}
        self._tokens: dict[tuple[str, str], str] = {}

    def mask_text(self, text: str) -> str:
        """Mask recognized non-overlapping spans without modifying other source facts."""
        spans: list[tuple[int, int, str]] = []
        for category, pattern, group in PATTERNS:
            for match in pattern.finditer(text):
                start, end = match.span(group)
                if not any(start < right and end > left for left, right, _ in spans):
                    spans.append((start, end, category))
        for start, end, category in sorted(spans, reverse=True):
            raw = text[start:end]
            key = category, raw
            if key not in self._tokens:
                token = f"{self.prefix}_{category.upper()}_{len(self.values) + 1}__"
                self._tokens[key] = token
                self.values[token] = key
            text = text[:start] + self._tokens[key] + text[end:]
        return text

    def mask_value(self, value: Any) -> Any:
        """Copy a JSON-compatible value with consistent aliases in strings and keys."""
        if isinstance(value, str):
            return self.mask_text(value)
        if isinstance(value, list):
            return [self.mask_value(item) for item in value]
        if isinstance(value, dict):
            return {self.mask_text(key): self.mask_value(item) for key, item in value.items()}
        return value

    def restore_value(self, value: Any) -> Any:
        """Restore only aliases created by this call, before source validation."""
        if isinstance(value, str):
            for token, (_, original) in self.values.items():
                value = value.replace(token, original)
            return value
        if isinstance(value, list):
            return [self.restore_value(item) for item in value]
        if isinstance(value, dict):
            return {
                self.restore_value(key): self.restore_value(item) for key, item in value.items()
            }
        return value

    def audit_mapping(self) -> dict:
        """Describe the private reversible mapping; callers must never log this payload."""
        return {
            "policy_version": PRIVACY_POLICY_VERSION,
            "counts": dict(Counter(category for category, _ in self.values.values())),
            "local_mapping": [
                {"alias": token, "classification": category, "original": raw}
                for token, (category, raw) in self.values.items()
            ],
        }
