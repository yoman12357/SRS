"""Natural certificate lifecycle verbs remain separate, source-bound and observable."""

import json
import threading
import time
from pathlib import Path

import pytest

from cybersrs.atomic_requirements import generate_atomic_requirements
from cybersrs.source_obligations import source_obligations

from .test_atomic_source_generation import SourceCriterionProvider
from .test_semantic_source_cases import case_analysis

CASES = json.loads(
    (Path(__file__).parent / "fixtures/remediation_certificate_cases.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["key"])
def test_complete_new_briefs_compile_with_source_bound_observable_tests(case, analysis):
    """The actual complete-section validator must pass without dropping source actions."""
    evidence, interpreted = case_analysis(case, analysis)
    units = [u for e in evidence for u in source_obligations(e)]
    if case["key"] == "certificates":
        for action, target in [
            ("review", "certificate requests"),
            ("approve", "certificate issuance"),
            ("renew", "certificates"),
            ("revoke", "compromised certificates"),
            ("track", "certificate status"),
        ]:
            expected = (
                "The system shall allow Authorized certificate administrators to "
                f"{action} {target}."
            )
            assert any(
                u.action == action
                and u.statement == expected
                for u in units
            )
        assert not any("requests, approve" in u.statement for u in units)
    previous = {}
    for name in ("functional", "nonfunctional"):
        content, provenance = generate_atomic_requirements(
            SourceCriterionProvider(),
            name,
            evidence,
            interpreted,
            [],
            previous,
            threading.Event(),
            time.monotonic() + 10,
            max_test_repairs=0,
        )
        assert not provenance["repaired_test_keys"]
        previous[name] = content
