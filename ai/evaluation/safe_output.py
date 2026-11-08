"""PII-safe console output helpers for local evaluation commands."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def print_case_header(
    case: Mapping[str, Any],
    *,
    variant: str | None = None,
) -> None:
    """Print allow-listed case metadata without exposing its description."""
    case_id = str(case.get("id", "unknown"))
    category = str(case.get("category", "unknown"))
    description_length = len(str(case.get("description", "")))
    expected = case.get("expected_categories", [])
    expected_categories: Sequence[object] = expected if isinstance(expected, list) else []
    variant_suffix = f" [{variant}]" if variant else ""

    print(f"\n{'=' * 60}")
    print(f"Running case: {case_id}{variant_suffix} ({category})")
    print(f"Description length: {description_length} characters (content redacted)")
    print(f"Expected categories: {[str(item) for item in expected_categories]}")
    print("=" * 60)
