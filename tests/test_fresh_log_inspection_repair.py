"""The real VPN database/time-window inventions must not anchor corrective tests."""

import copy
import threading
import time

from cybersrs.evidence import build_evidence
from cybersrs.requirement_repair import repair_canonical_acceptance
from cybersrs.schemas import AcceptanceTestRepair
from cybersrs.source_completion import source_role_denial_statement

from .conftest import requirement
from .test_permission_verification import criterion

SOURCE = (
    "Administrators manage remote-access permissions; support operators may inspect "
    "connection logs but cannot grant permissions."
)


def test_compound_source_denial_does_not_invent_exclusive_admin_authority():
    """Use the exact source actor/denial, keeping generic administration nonexclusive."""
    bad = "Support operators shall not grant permissions; only administrators may grant them."
    assert (
        source_role_denial_statement(SOURCE, bad) == "support operators cannot grant permissions."
    )
    assert source_role_denial_statement(SOURCE, "Administrators may manage permissions.") is None
    assert source_role_denial_statement(SOURCE, "Support operators may inspect logs.") is None


def test_semantic_log_test_repair_discards_bad_example_and_preserves_valid_denial(analysis):
    """Exercise the real field repair and independently reject the old database/window test."""
    row = requirement(
        "Support operators may inspect connection logs but cannot grant permissions.", "E-001"
    ) | {"id": "FR-002"}
    bad = criterion(
        "A support operator requests connection logs from the past 24 hours",
        "The system retrieves the connection logs from a database",
        "The support operator can inspect the retrieved connection logs",
    )
    denial = criterion(
        "A support operator has a controlled test identity",
        "The support operator attempts to grant remote-access permissions",
        "The permission-grant action is denied and permission state remains unchanged",
    )
    row["acceptance_criteria"] = [bad, denial]
    before = copy.deepcopy(row)
    good = criterion(
        "A support-operator test identity and existing connection-log fixture are available",
        "The support operator requests inspection of connection logs",
        "The support operator can inspect the requested connection logs",
    )
    admin = requirement("Administrators shall manage remote-access permissions.", "E-001") | {
        "id": "FR-001"
    }

    class Provider:
        """Return one corrected authored criterion, without a candidate-copying loop."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            assert schema is AcceptanceTestRepair
            assert context["retry_from_source"]
            assert "rejected_criterion" not in context
            old = schema(requirement_id=row["id"], acceptance_criterion=bad)
            assert any("unsupported_quantitative_commitment" in error for error in validate(old))
            result = schema(requirement_id=row["id"], acceptance_criterion=good)
            assert validate(result) == []
            return result, {"model": "test-qwen", "attempts": 1}

    output, _, calls = repair_canonical_acceptance(
        Provider(),
        "functional",
        {"requirements": [row]},
        build_evidence(SOURCE, []),
        analysis.model_copy(update={"assessments": []}),
        [],
        {"functional": {"requirements": [admin]}},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert calls == 1
    assert output["requirements"][0]["acceptance_criteria"] == [good, denial]
    assert row == before
