"""Exercise the actual atomic compiler/provider/schema boundary for all four stakeholder briefs."""

import re
import threading
import time

import pytest
from pydantic import ValidationError

from cybersrs.acceptance_grounding import (
    acceptance_logging_issues,
    acceptance_response_issues,
    preserve_source_outcome,
)
from cybersrs.atomic_requirements import (
    AtomicCriterion,
    correction_guidance,
    generate_atomic_requirements,
)
from cybersrs.compact_requirements import generate_compact_requirements
from cybersrs.evidence import build_evidence
from cybersrs.provider import GenerationError
from cybersrs.source_obligations import criterion_target_issues, source_obligations

from .test_semantic_source_cases import CASES, MUST_HAVE, case_analysis


class SourceCriterionProvider:
    """An inert test author; assertions still run the real complete section validator."""

    model_name = "test-criterion-author"

    def generate(self, system, context, schema, cancel, deadline, validate):
        """Return observable source-bound fixtures rather than synthetic successful SRS content."""
        assert context["source_evidence"] == []
        candidate = {}
        observed = {
            "provide": "are provided",
            "use": "is used",
            "separate": "is separated",
            "monitor": "are displayed",
            "detect": "are identified",
            "generate": "are generated",
            "configure": "are configured",
            "review": "are returned",
            "revoke": "is revoked",
            "inspect": "are inspected",
            "support": "are supported",
            "protect": "are protected",
            "quarantine": "are quarantined",
            "maintain": "are maintained",
            "integrate": "is integrated",
            "collect": "are collected",
            "investigate": "are presented",
            "record": "are saved",
            "log": "are logged",
            "control": "is controlled",
            "require": "is required",
            "assign": "is assigned",
            "grant": "are granted",
            "modify": "are modified",
            "suspend": "are suspended",
            "terminate": "are terminated",
            "define": "are defined",
            "initiate": "are initiated",
            "submit": "are submitted",
            "track": "are tracked",
            "restore": "are restored",
            "restrict": "is restricted",
            "approve": "is approved",
            "renew": "are renewed",
            "close": "are closed",
            "register": "are registered",
            "authenticate": "are authenticated",
            "change": "is updated",
            "isolate": "are isolated",
            "create": "are created",
            "update": "are updated",
            "enforce": "are enforced",
            "release": "are released",
            "manage": "are managed",
        }
        for unit in context["source_obligations"]:
            body = unit["operation"]
            if body.startswith("support") and "approved" not in body:
                assert "approval" not in unit["test_focus"]
            actor = (
                "A tester with relevant source fixtures"
                if unit["actor"] == "system"
                else (unit["actor"] + " with the stated permissions")
            )
            verb, _, obj = body.partition(" ")
            quality = unit["kind"] == "nonfunctional"
            parts = re.split(r"\s+(when|after|upon|before|during|while)\s+", obj, maxsplit=1)
            subject = parts[0]
            observed_result = "" if quality else f"{subject} {observed[verb]}"
            if len(parts) == 3:
                observed_result += " " + parts[1] + " " + parts[2]
            if quality:
                assert context["source_evidence"] == []
            candidate[unit["key"]] = {
                "given": "The acceptance targets are awaiting stakeholder confirmation"
                if quality
                else actor,
                "when": "The analyst reviews the attribute acceptance plan"
                if quality
                else f"The tester initiates the {verb} operation",
                "then": f"The {obj} acceptance plan identifies its metrics as TBD"
                if quality
                else f"Observed result: {observed_result}",
                "method": "inspection" if quality else "test",
                "observable_evidence": "External test capture of the resulting state",
            }
        parsed = schema.model_validate(candidate)
        assert validate(parsed) == []
        return parsed, {"model": self.model_name, "attempts": 1}


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["key"])
def test_compact_dispatch_preserves_quality_when_the_same_source_has_a_functional_row(
    case, analysis
):
    """Exercise the actual caller, including the endpoint source's sole secure quality goal."""
    evidence, interpreted = case_analysis(case, analysis)
    predecessors = {}
    for name in ("functional", "nonfunctional"):
        content, _ = generate_compact_requirements(
            SourceCriterionProvider(),
            name,
            evidence,
            interpreted,
            [],
            predecessors,
            threading.Event(),
            time.monotonic() + 5,
        )
        predecessors[name] = content
    assert any(
        "secure" in row["statement"] for row in predecessors["nonfunctional"]["requirements"]
    )


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["key"])
def test_atomic_generation_keeps_all_behaviors_functional_and_quality_separate(case, analysis):
    """A model omission cannot change the frozen source statement inventory."""
    evidence, analysis = case_analysis(case, analysis)
    provider = SourceCriterionProvider()
    predecessors = {}
    for name in ("functional", "nonfunctional"):
        content, provenance = generate_atomic_requirements(
            provider,
            name,
            evidence,
            analysis,
            [],
            predecessors,
            threading.Event(),
            time.monotonic() + 5,
        )
        assert provenance["source_obligations_version"]
        assert all(row["acceptance_criteria"] for row in content["requirements"])
        assert all(len(row["evidence_ids"]) == 1 for row in content["requirements"])
        predecessors[name] = content
    functional = [row["statement"].casefold() for row in predecessors["functional"]["requirements"]]
    for phrase in MUST_HAVE[case["key"]]:
        assert any(phrase in statement for statement in functional)
    assert all(
        row["statement"].startswith(("The system shall remain ", "The system shall be "))
        for row in predecessors["nonfunctional"]["requirements"]
    )
    expected = {unit.statement for fact in evidence for unit in source_obligations(fact)}
    actual = {
        row["statement"] for section in predecessors.values() for row in section["requirements"]
    }
    assert actual == expected


def test_generic_processing_or_wrong_operation_is_not_an_acceptance_result():
    """The source card cannot receive a test that only says its request was processed."""
    case = next(case for case in CASES if case["key"] == "email")
    from cybersrs.evidence import build_evidence

    unit = next(
        unit
        for fact in build_evidence(case["description"], [])
        for unit in source_obligations(fact)
        if unit.action == "quarantine"
    )
    criterion = {
        "given": "A relevant test input is present",
        "when": "The request is processed",
        "then": "The request is processed",
        "method": "test",
        "observable_evidence": "External test capture of state",
    }
    assert criterion_target_issues(unit, criterion)


def test_live_email_logging_side_effect_keeps_the_authored_blocking_outcome():
    """Reproduce the actual rejected base-model result without replacing its valid outcome."""
    source = next(case for case in CASES if case["key"] == "email")["description"].split(". ")[0]
    candidate = {
        "given": "A controlled message contains a malicious attachment",
        "when": "The gateway processes that message",
        "then": "The system blocks the message and logs the event in a "
        "test-instrumented response state capture file.",
        "method": "test",
        "observable_evidence": "Test-instrumented response state capture shows the blocked message",
    }
    normalized = preserve_source_outcome(source, candidate)
    assert normalized["then"] == "The system blocks the message."
    assert normalized["given"] == candidate["given"] and normalized["when"] == candidate["when"]


def test_email_quarantine_isolation_is_not_endpoint_isolation():
    """The response guard must distinguish an explicitly quarantined email from a device action."""
    source = (
        "The system shall detect suspicious messages and quarantine potentially harmful emails."
    )
    criterion = {"then": "The system quarantines the email and isolates it from user access"}
    assert not acceptance_response_issues(source, criterion)
    assert acceptance_response_issues(
        source, {"then": "The endpoint is isolated from network access"}
    )
    assert acceptance_response_issues(
        "Detect unusual login behavior.", {"then": "The account is locked"}
    )


@pytest.mark.parametrize(
    "rejected_outcome",
    [
        "A security alert is generated within 5 seconds",
        "A security alert is generated with an error message",
    ],
)
@pytest.mark.parametrize("needs_followup", [False, True])
def test_atomic_repair_changes_only_the_rejected_outcome(
    analysis, rejected_outcome, needs_followup
):
    """Replay the field-only correction route while all valid outcomes remain frozen."""
    source = "The system should inspect incoming email traffic and generate security alerts."
    evidence = build_evidence(source, [])
    target = analysis.model_copy(
        update={
            "assessments": [
                analysis.assessments[0].model_copy(
                    update={"evidence_id": "E-001", "sections": ["functional"]}
                )
            ]
        }
    )
    originals = {
        "E-001_O01": {
            "given": "Incoming test email traffic is present",
            "when": "The tester requests traffic inspection",
            "then": "The test email traffic is inspected",
            "method": "test",
            "observable_evidence": "External test capture of the resulting state",
        },
        "E-001_O02": {
            "given": "A test email security alert condition is present",
            "when": "The tester initiates the alert condition",
            "then": rejected_outcome,
            "method": "test",
            "observable_evidence": "External test capture of the resulting state",
        },
    }

    class Provider:
        """Reject an unprovided deadline and return only its observed-outcome replacement."""

        model_name = "test-adapter"
        patch_calls = 0

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Assert unrelated fields are unavailable to the corrective model."""
            if "tests_to_repair" not in context:
                candidate = schema.model_validate(originals)
                assert validate(candidate)
                raise GenerationError(
                    "section_validation_failed:deadline",
                    rejected_candidate=candidate.model_dump(),
                    rejected_model="test-base",
                    attempts=2,
                )
            assert set(context["tests_to_repair"]) == {"E-001_O02"}
            self.patch_calls += 1
            assert (
                context["tests_to_repair"]["E-001_O02"]["frozen_fields"]["when"]
                == originals["E-001_O02"]["when"]
            )
            with pytest.raises(ValidationError):
                schema.model_validate(
                    {
                        "E-001_O02": {
                            "then": "A security alert is generated",
                            "given": "changed fixture",
                        }
                    }
                )
            if needs_followup and self.patch_calls == 1:
                rejected = schema.model_validate(
                    {
                        "E-001_O02": {
                            "then": "A security alert is generated and delivered to "
                            "the security operations center"
                        }
                    }
                )
                assert validate(rejected)
                raise GenerationError(
                    "section_validation_failed:alert_destination",
                    rejected_candidate=rejected.model_dump(),
                    rejected_model="test-base",
                    attempts=1,
                )
            result = schema.model_validate({"E-001_O02": {"then": "A security alert is generated"}})
            assert validate(result) == []
            return result, {"model": "test-base", "attempts": 1}

    result, metadata = generate_atomic_requirements(
        Provider(),
        "functional",
        evidence,
        target,
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
        max_test_repairs=2 if needs_followup else 1,
    )
    assert result["requirements"][0]["acceptance_criteria"][0] == originals["E-001_O01"]
    assert (
        result["requirements"][1]["acceptance_criteria"][0]["then"]
        == "A security alert is generated"
    )
    assert set(metadata["repaired_test_keys"]) == {"E-001_O02"}
    assert metadata["attempts"] == (4 if needs_followup else 3)


def test_primary_test_witness_cannot_prescribe_an_unrequested_production_log():
    """The native and Python schemas both constrain witnesses to external test captures."""
    with pytest.raises(ValidationError):
        AtomicCriterion(
            given="A controlled message is present",
            when="The gateway inspects it",
            then="The message is inspected",
            method="test",
            observable_evidence="Production logs show the inspection event",
        )


def test_corrective_feedback_does_not_echo_rejected_live_behavior_code():
    """The actual rejected dashboard wording must not become the corrective task's content."""
    instructions = correction_guidance(
        ["E-003_O03:unsupported_live_behavior", "FR-010:unsupported_source_detail_live_behavior"]
    )
    assert instructions == [
        "Describe the resulting content or state; timing and quantities are undecided."
    ]
    assert "live" not in " ".join(instructions)


def test_general_email_protection_does_not_confirm_a_recipient_notification():
    """A broad protection goal cannot select a delivery response absent the stakeholder source."""
    fact = build_evidence("Design an email gateway that protects users from malicious emails.", [])[
        0
    ]
    unit = next(unit for unit in source_obligations(fact) if unit.action == "protect")
    criterion = {
        "given": "An email with a malicious attachment is submitted",
        "when": "The gateway evaluates the email",
        "then": "The gateway blocks the email and sends a notification to the recipient",
    }
    assert "criterion_protection_response_undecided" in criterion_target_issues(unit, criterion)


@pytest.mark.parametrize(
    "suffix", ["is recorded in the system logs", "recorded in the system logs"]
)
def test_preserve_alert_outcome_without_added_passive_log_side_effect(suffix):
    """Keep the authored alert result while removing only its unsupported trailing log action."""
    original = {
        "given": "A controlled security alert condition is present",
        "when": "The alert condition is submitted",
        "then": "A security alert is generated and " + suffix,
        "observable_evidence": "External test capture of the resulting state",
    }
    corrected = preserve_source_outcome("Generate security alerts.", original)
    assert corrected == original | {"then": "A security alert is generated."}
    assert (
        preserve_source_outcome("Generate security alerts and record system logs.", original)
        == original
    )


@pytest.mark.parametrize("modifier", ["real-time", "real time", "live"])
def test_unsupported_display_timing_modifier_preserves_the_authored_event_result(modifier):
    """The exact observed dashboard result survives; a new refresh promise does not."""
    original = {
        "then": f"The dashboard displays {modifier} email security events",
        "observable_evidence": "External test capture of the resulting response",
    }
    assert preserve_source_outcome("Provide a dashboard for email security events.", original) == (
        original | {"then": "The dashboard displays email security events"}
    )
    assert preserve_source_outcome(f"Provide a {modifier} dashboard.", original) == original


def test_postfixed_display_timing_modifier_keeps_the_reported_state():
    """Replay the final firewall repair's suffix without turning it into a refresh promise."""
    original = {
        "then": "The system reports blocked and allowed traffic in real time.",
        "observable_evidence": "External test capture of the resulting state",
    }
    assert preserve_source_outcome("Monitor blocked and allowed traffic.", original) == (
        original | {"then": "The system reports blocked and allowed traffic."}
    )


def test_alert_generation_does_not_confirm_delivery_to_a_new_soc():
    """The actual firewall repair must not invent a new recipient integration."""
    unit = source_obligations(build_evidence("The system should generate security alerts.", [])[0])[
        0
    ]
    issues = criterion_target_issues(
        unit,
        {
            "given": "A controlled security alert condition is present",
            "when": "The security alert condition is submitted",
            "then": "An alert is generated and delivered to the security operations center",
        },
    )
    assert "criterion_alert_destination_undecided" in issues


@pytest.mark.parametrize(
    "scope",
    [
        "filtering decisions and administrator actions",
        "security events and administrator actions",
        "firewall policy changes and administrative actions",
    ],
)
def test_maintaining_event_audit_logs_authorizes_the_requested_event_entries(scope):
    """Maintain logs OF events requests event recording; inspecting/retaining old logs does not."""
    source = "The system should maintain audit logs of " + scope + "."
    criterion = {
        "then": "The system records the stated event in the audit log",
        "observable_evidence": "External test capture of the resulting state",
    }
    assert not acceptance_logging_issues(source, criterion)
    assert acceptance_logging_issues("The administrator should inspect audit logs.", criterion)


def test_repeated_initiation_repairs_the_trigger_and_result_together(analysis):
    """Replay the Wi-Fi support test that repeated a declarative source claim as its trigger."""
    evidence = build_evidence(
        "The system should support university-managed and approved personal devices "
        "for wireless access.",
        [],
    )
    target = analysis.model_copy(
        update={
            "assessments": [
                analysis.assessments[0].model_copy(
                    update={"evidence_id": "E-001", "sections": ["functional"]}
                )
            ]
        }
    )
    original = {
        "given": "Controlled university-managed and approved personal test devices are present",
        "when": "The system supports university-managed and approved personal devices",
        "then": "The system supports university-managed and approved personal devices",
        "method": "test",
        "observable_evidence": "External test capture of the resulting state",
    }

    class Provider:
        """Return an authored operational trigger only when that invalid field is unlocked."""

        model_name = "test-base"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Exercise full validation before and after the constrained patch."""
            if "tests_to_repair" not in context:
                candidate = schema.model_validate({"E-001": original})
                assert validate(candidate)
                raise GenerationError(
                    "section_validation_failed:criterion_result_repeats_initiation",
                    rejected_candidate=candidate.model_dump(),
                    rejected_model="test-base",
                    attempts=1,
                )
            assert set(schema.model_json_schema()["$defs"]["CriterionPatch0"]["properties"]) == {
                "when",
                "then",
            }
            assert (
                context["tests_to_repair"]["E-001"]["frozen_fields"]["given"] == original["given"]
            )
            result = schema.model_validate(
                {
                    "E-001": {
                        "when": "Each stated test device initiates a wireless connection",
                        "then": "A wireless connection is established "
                        "using each stated device type",
                    }
                }
            )
            assert not validate(result)
            return result, {"model": "test-base", "attempts": 1}

    result, _ = generate_atomic_requirements(
        Provider(), "functional", evidence, target, [], {}, threading.Event(), time.monotonic() + 5
    )
    assert result["requirements"][0]["acceptance_criteria"][0]["given"] == original["given"]


def test_detection_source_does_not_confirm_automatic_alert_generation():
    """The saved endpoint outcomes added alerts to a detection-only source."""
    unit = source_obligations(
        build_evidence("The platform should detect unusual login behavior.", [])[0]
    )[0]
    criterion = {
        "given": "A controlled unusual-login example is present",
        "when": "The example is submitted to the detector",
        "then": "An alert is generated and its resulting state is captured externally",
    }
    assert "criterion_detection_output_undecided" in criterion_target_issues(unit, criterion)
    supported = source_obligations(
        build_evidence(
            "The platform should detect unusual login behavior and generate alerts.", []
        )[0]
    )[0]
    assert "criterion_detection_output_undecided" not in criterion_target_issues(
        supported, criterion
    )


def test_device_use_success_is_an_observed_support_result():
    """A corrected Wi-Fi result can express success without the literal word support."""
    fact = build_evidence(
        "The system should support university-managed and approved personal devices.", []
    )[0]
    unit = source_obligations(fact)[0]
    assert not criterion_target_issues(
        unit,
        {
            "given": "Controlled examples of each stated device type are present",
            "when": "The devices initiate their stated use",
            "then": "Each stated device's requested operation succeeds",
        },
    )


@pytest.mark.parametrize(
    "outcome",
    [
        "The requested alert exists; its destination is undecided.",
        "A security alert is emitted",
        "A security alert is produced",
    ],
)
def test_generated_alert_state_accepts_normal_observable_paraphrases(outcome):
    """The actual rejected alert-exists repair must not fail solely on verb vocabulary."""
    unit = source_obligations(build_evidence("The system should generate security alerts.", [])[0])[
        0
    ]
    assert not criterion_target_issues(
        unit,
        {
            "given": "A controlled security alert condition is present",
            "when": "The condition is submitted",
            "then": outcome,
        },
    )


def test_review_outcome_requires_reviewed_content_not_only_instrumentation():
    """The email repair's new inspection record did not observe the requested message review."""
    unit = source_obligations(
        build_evidence(
            "The system should allow authorized administrators to review quarantined messages.", []
        )[0]
    )[0]
    criterion = {
        "given": "An authorized administrator and a quarantined message are present",
        "when": "The administrator requests to review the message",
        "then": "An inspection record is produced and stored for external test capture",
    }
    assert "criterion_review_result_is_only_instrumentation" in criterion_target_issues(
        unit, criterion
    )
    assert not criterion_target_issues(
        unit, criterion | {"then": "The requested quarantined message is returned for examination"}
    )
