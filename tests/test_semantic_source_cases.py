"""Four independent source-obligation regressions using the supplied briefs and observed defects."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from cybersrs.clarification_policy import (
    consolidate_document_decisions,
    decision_topics,
    deduplicate_decisions,
    normalize_analysis_decisions,
)
from cybersrs.evidence import build_evidence
from cybersrs.policy_applicability import compliance_requirement_context
from cybersrs.schemas import Evidence, EvidenceAssessment
from cybersrs.source_detail_policy import unsupported_observed_fields, unsupported_source_details
from cybersrs.source_obligations import (
    missing_obligation_keys,
    normalize_requirement_sections,
    source_obligations,
)
from cybersrs.srs_presentation import stakeholder_table
from cybersrs.validation import validate_section

CASES = json.loads((Path(__file__).parent / "fixtures/semantic_source_cases.json").read_text())
MUST_HAVE = {
    "wifi": [
        "provide wireless access to students, faculty, staff, and guests",
        "use centralized authentication",
        "use role-based access control",
        "separate guest access",
        "monitor active wireless sessions",
        "detect repeated authentication failures",
        "detect unauthorized access attempts",
        "generate security alerts",
        "configure wireless access policies",
        "review connected devices",
        "revoke access",
        "inspect audit logs",
        "support university-managed and approved personal devices",
    ],
    "email": [
        "protect students, faculty, staff, and administrators",
        "inspect incoming and outgoing email traffic",
        "detect suspicious messages",
        "quarantine potentially harmful emails",
        "generate security alerts",
        "authorized administrators to review quarantined messages",
        "authorized administrators to release quarantined messages",
        "maintain audit logs of filtering decisions and administrator actions",
        "integrate with the university identity system",
        "provide a dashboard for monitoring email security events",
    ],
    "endpoint": [
        "collect system events, authentication activity, process information, and security alerts",
        "detect unusual login behavior",
        "detect repeated failed authentication",
        "detect suspicious process activity",
        "detect unauthorized configuration changes",
        "review alerts",
        "investigate affected devices",
        "record investigation notes",
        "change alert status",
        "isolate compromised endpoints when necessary",
        "maintain audit logs of security events and administrator actions",
        "provide a centralized dashboard",
    ],
    "firewall": [
        "manage firewall policies across academic, administrative, research, hostel, "
        "and guest networks",
        "authorized network administrators to create firewall rules",
        "authorized network administrators to review firewall rules",
        "authorized network administrators to update firewall rules",
        "authorized network administrators to revoke firewall rules",
        "enforce access restrictions between network segments",
        "monitor blocked and allowed traffic",
        "generate alerts for suspicious",
        "maintain audit logs of firewall policy changes and administrative actions",
        "provide a dashboard",
        "support multiple campus buildings",
    ],
}


def case_analysis(case, analysis):
    """Use an intentionally misclassified model analysis to test source-driven correction."""
    evidence = build_evidence(case["description"], [])
    result = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id=fact.id,
                    kind="requirement",
                    sections=["nonfunctional"],
                    explanation="Synthetic initial misclassification.",
                )
                for fact in evidence
            ]
        }
    )
    return evidence, normalize_requirement_sections(result, evidence)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["key"])
def test_source_inventory_preserves_independent_operations_and_literal_traceability(case, analysis):
    """Expected source operations are hand-enumerated independently of the splitter."""
    evidence, result = case_analysis(case, analysis)
    units = [unit for fact in evidence for unit in source_obligations(fact)]
    statements = [unit.statement.casefold() for unit in units]
    assert len({unit.key for unit in units}) == len(units)
    for phrase in MUST_HAVE[case["key"]]:
        assert any(phrase in statement for statement in statements), phrase
    if case["key"] == "endpoint":
        collection = next(unit.statement for unit in units if unit.action == "collect")
        assert "university servers and managed endpoints" in collection
    if case["key"] == "firewall":
        assert "centralized" in next(unit.statement for unit in units if unit.action == "manage")
    for unit in units:
        assert unit.quote == next(fact.quote for fact in evidence if fact.id == unit.evidence_id)
        sections = next(
            item.sections for item in result.assessments if item.evidence_id == unit.evidence_id
        )
        assert unit.section in sections
        assert not unsupported_source_details(unit.statement, evidence)
    # Revoke/release/change are independent statements, not just criteria of another operation.
    assert all(
        sum(phrase in statement for statement in statements) >= 1
        for phrase in MUST_HAVE[case["key"]]
    )


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["key"])
def test_deleting_any_generated_obligation_is_detected_in_normative_content(case, analysis):
    """A matching rationale/test cannot hide deletion of an actual canonical statement."""
    evidence, _ = case_analysis(case, analysis)
    units = [unit for fact in evidence for unit in source_obligations(fact)]
    rows = [{"statement": unit.statement, "evidence_ids": [unit.evidence_id]} for unit in units]
    for index, unit in enumerate(units):
        remaining = deepcopy(rows[:index] + rows[index + 1 :])
        for row in remaining:
            row["rationale"] = unit.statement
            row["acceptance_criteria"] = [{"then": unit.statement}]
        fact = next(fact for fact in evidence if fact.id == unit.evidence_id)
        assert unit.key in missing_obligation_keys(fact, remaining, unit.section), unit


def test_observed_email_quarantine_and_alert_loss_is_rejected(analysis):
    """Run the actual saved bad email requirements through the public validator."""
    case = next(case for case in CASES if case["key"] == "email")
    evidence, normalized = case_analysis(case, analysis)
    errors = validate_section(
        "functional", case["rejected_original_sections"]["functional"], evidence, normalized, [], {}
    )
    fact = next(fact for fact in evidence if "quarantine potentially harmful" in fact.quote)
    for unit in source_obligations(fact):
        if unit.action in {"quarantine", "generate"}:
            assert f"{fact.id}:missing_explicit_obligation:{unit.key}" in errors


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["key"])
@pytest.mark.parametrize(
    "claim",
    [
        "The approved device is registered in the device inventory.",
        "The platform monitors device health and patch levels.",
        "The system verifies device compliance before permitting access.",
        "Collected events arrive via secure data feeds.",
        "The system processes events in real-time.",
        "Predefined behavioral thresholds determine suspicious activity.",
        "The platform requires certificate-based device authentication.",
        "An alert is returned within 5 seconds.",
        "The system maintains service with no performance degradation.",
        "The collected data conforms to the defined schema.",
    ],
)
def test_unsupported_mandatory_choices_rejected_for_all_four_sources(case, claim):
    """General adjectives and approved devices do not authorize a concrete implementation."""
    assert unsupported_source_details(claim, build_evidence(case["description"], []))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["key"])
def test_relevant_semantic_question_duplicates_merge_and_external_topics_are_rejected(case):
    """Preserve separate retention/field questions while excluding imported product features."""
    evidence = build_evidence(case["description"], [])
    questions = deduplicate_decisions(
        [
            "Which fields must the audit logs contain?",
            "What specific data fields should be included in audit logs?",
            "What retention period is required for audit logs?",
            "How long should audit logs be retained?",
            "How will device-health monitoring and patch levels be implemented?",
            "Will certificate-based device authentication be used?",
            "How are dynamic risk-based access policies defined?",
            "Which mandatory regulatory framework applies?",
        ],
        evidence,
    )
    assert len(questions) == 2
    assert {decision_topics(value, evidence)[0][0] for value in questions} == {
        "audit_fields",
        "audit_retention",
    }


def test_guest_network_is_not_a_guest_user_or_scenario_actor(complete_document):
    """Network-zone modifiers cannot manufacture a guest application user."""
    case = next(case for case in CASES if case["key"] == "firewall")
    evidence = build_evidence(case["description"], [])
    document = complete_document.model_copy(deep=True)
    document.evidence = evidence
    roles = [row[0] for row in stakeholder_table(document).rows]
    assert "Admin" in roles and "User" not in roles
    analysis = normalize_analysis_decisions(
        document.analysis.model_copy(
            update={
                "stakeholders": ["Guest users", "Network administrators"],
            }
        ),
        evidence,
    )
    assert analysis.stakeholders == ["Network administrators"]
    human = build_evidence(
        "Students and guests access services; guest networks remain isolated.", []
    )
    document.evidence = human
    assert "User" in [row[0] for row in stakeholder_table(document).rows]


def test_canonical_decisions_have_one_question_and_reusable_references(analysis):
    """Multiple sections can link one decision without copying its question text."""
    evidence = build_evidence("The system maintains audit logs of administrator actions.", [])
    analysis = analysis.model_copy(
        update={
            "questions": [],
            "unresolved_decisions": [
                "Which fields must the audit logs contain?",
            ],
        }
    )
    sections = {
        "functional": {
            "requirements": [
                {
                    "id": "FR-001",
                    "evidence_ids": ["E-001"],
                    "unresolved_decisions": ["What fields should the audit logs include?"],
                }
            ]
        },
        "compliance": {
            "open_decisions": ["Which specific fields should be included in audit logs?"]
        },
    }
    result = consolidate_document_decisions(analysis, sections, evidence)
    assert len(result.questions) == 1 and not result.unresolved_decisions
    ref = "Decision " + result.questions[0].id + " is TBD."
    assert sections["functional"]["requirements"][0]["unresolved_decisions"] == [ref]
    assert sections["compliance"]["open_decisions"] == [ref]
    assert result.questions[0].evidence_ids == ["E-001"]


def test_distinct_detection_decisions_survive_semantic_deduplication():
    """Login anomalies and repeated failures are different decisions, not mere rephrasings."""
    case = next(case for case in CASES if case["key"] == "endpoint")
    evidence = build_evidence(case["description"], [])
    values = deduplicate_decisions(
        [
            "What thresholds define repeated authentication failures?",
            "Which conditions trigger repeated failed authentication?",
            "What counts as unusual login behavior?",
            "What conditions define unusual login behavior?",
        ],
        evidence,
        canonical=True,
    )
    assert len(values) == 2
    assert {key for value in values for key, _ in decision_topics(value, evidence)} == {
        "detection:failed_authentication",
        "detection:unusual_login",
    }


def test_observed_rag_presuppositions_are_removed_without_losing_event_format_decision():
    """A collector needs input formats, not an invented normalization or encryption feature."""
    case = next(case for case in CASES if case["key"] == "endpoint")
    evidence = build_evidence(case["description"], [])
    values = deduplicate_decisions(
        [
            "What encryption method will be used for data feeds between departments and servers?",
            "How will device-level policies be enforced on personal devices?",
            "What schema will be used to normalize collected events from multiple sources?",
            "Which event formats must be collected from the stated sources?",
        ],
        evidence,
        canonical=True,
    )
    assert values == ["Which event formats must be collected from the stated sources?"]


@pytest.mark.parametrize(
    "claim",
    [
        "The platform shall use certificate-based device authentication.",
        "The system shall verify device compliance before access.",
        "The system shall collect events using secure data feeds.",
        "The system shall generate an alert within 5 seconds.",
        "The service shall run with no performance degradation.",
    ],
)
def test_explicit_stakeholder_choices_are_not_rejected_as_assumptions(claim):
    """The same concrete choice is legitimate when the stakeholder actually supplied it."""
    assert not unsupported_source_details(
        claim, [Evidence(id="E-001", source="description", quote=claim)]
    )


def test_product_log_fields_need_confirmation_but_test_capture_fields_are_instrumentation():
    """Do not turn an audit-log request into an unstated mandatory record schema."""
    evidence = build_evidence("The platform maintains audit logs of administrator actions.", [])
    outcome = "The audit entry contains a timestamp and user ID."
    assert unsupported_observed_fields(outcome, evidence) == ["timestamp", "user ID"]
    assert not unsupported_observed_fields("The test collector records a timestamp.", evidence)
    confirmed = build_evidence("Audit entries must contain a timestamp and user ID.", [])
    assert not unsupported_observed_fields(outcome, confirmed)


def test_generated_decision_references_survive_section_regeneration(analysis):
    """A linked question reference must not be removed or rendered as a second question."""
    evidence = build_evidence("The system maintains audit logs of administrator actions.", [])
    sections = {
        "functional": {
            "requirements": [
                {
                    "id": "FR-001",
                    "evidence_ids": ["E-001"],
                    "unresolved_decisions": ["Which fields must the audit logs contain?"],
                }
            ]
        }
    }
    first = consolidate_document_decisions(
        analysis.model_copy(update={"questions": [], "unresolved_decisions": []}),
        sections,
        evidence,
    )
    ref = sections["functional"]["requirements"][0]["unresolved_decisions"][0]
    assert deduplicate_decisions([ref, ref], evidence) == [ref]
    assert deduplicate_decisions([ref], evidence, include_references=False) == []
    repeated = consolidate_document_decisions(first, sections, evidence)
    assert repeated.questions == first.questions
    assert sections["functional"]["requirements"][0]["unresolved_decisions"] == [ref]


@pytest.mark.parametrize(
    "text",
    [
        "Which antivirus vendor must the email security gateway integrate?",
        "Which ML model should detect suspicious email messages?",
        "Which endpoint agents must collect security events from university servers?",
    ],
)
def test_project_objects_do_not_make_unrequested_technology_questions_relevant(text):
    """Shared words such as email/server cannot launder a new implementation choice."""
    evidence = build_evidence(" ".join(case["description"] for case in CASES), [])
    assert not decision_topics(text, evidence)


def test_firewall_shared_rule_object_closes_the_administrator_permission_list():
    """System enforcement, monitoring and alerts must not become optional human-only controls."""
    case = next(case for case in CASES if case["key"] == "firewall")
    units = [
        unit
        for fact in build_evidence(case["description"], [])
        for unit in source_obligations(fact)
    ]
    for action in ("create", "review", "update", "revoke"):
        unit = next(unit for unit in units if unit.action == action)
        assert unit.statement.startswith("The system shall allow authorized network administrators")
    for action in ("enforce", "monitor", "generate"):
        unit = next(unit for unit in units if unit.action == action)
        assert unit.statement.startswith("The system shall " + action)


def test_plural_observed_log_fields_are_not_implicitly_authorized():
    """The latest rejected authored audit outcome used plural timestamps to bypass a word check."""
    evidence = build_evidence("Maintain audit logs of administrator actions.", [])
    assert unsupported_observed_fields("Logs contain timestamps and message IDs", evidence) == [
        "timestamp",
        "message ID",
    ]
    explicit = build_evidence("Audit logs contain timestamps and message IDs.", [])
    assert not unsupported_observed_fields("Logs contain timestamps and message IDs", explicit)


def test_wifi_summary_cannot_assert_an_unsupported_device_policy(analysis):
    """The actual live analysis summary had a new device-level capability outside the source."""
    case = next(case for case in CASES if case["key"] == "wifi")
    evidence = build_evidence(case["description"], [])
    candidate = analysis.model_copy(
        update={
            "summary": "The system supports device-level policies and administrator configuration."
        }
    )
    result = normalize_analysis_decisions(candidate, evidence)
    assert result.summary == " ".join(fact.quote for fact in evidence)
    assert not unsupported_source_details(result.summary, evidence)


def test_compliance_context_keeps_every_requirement_and_its_grounding(complete_document):
    """More atomic rows must not overflow context by repeating acceptance procedures here."""
    original = [row.model_dump() for row in complete_document.functional.requirements]
    result = compliance_requirement_context(original)
    assert len(result) == len(original)
    for actual, expected in zip(result, original, strict=True):
        assert actual == {
            key: expected[key] for key in ("id", "statement", "basis", "evidence_ids", "sources")
        }
        assert "acceptance_criteria" not in actual
    assert compliance_requirement_context([]) == []


def test_firewall_network_modifier_does_not_make_segment_enforcement_a_human_interaction(
    analysis, complete_document
):
    """Replay FR-006's empty actor selection caused by splitting a compound role label."""
    from cybersrs.scenario_projection import scenario_inventory
    from cybersrs.validation import interactive_requirement_ids

    case = next(case for case in CASES if case["key"] == "firewall")
    evidence = build_evidence(case["description"], [])
    interpreted = analysis.model_copy(update={"stakeholders": ["network administrators"]})
    units = [
        unit
        for fact in evidence
        for unit in source_obligations(fact)
        if unit.section == "functional"
    ]
    template = complete_document.functional.requirements[0].model_dump()
    rows = [
        template
        | {"id": f"FR-{index:03d}", "statement": unit.statement, "evidence_ids": [unit.evidence_id]}
        for index, unit in enumerate(units, 1)
    ]
    assert interactive_requirement_ids(rows, interpreted) == {f"FR-{i:03d}" for i in range(2, 6)}
    inventory = scenario_inventory({"functional": {"requirements": rows}}, evidence, interpreted)
    assert all(inventory["actor_options"].values())


def test_email_traffic_word_overlap_cannot_import_a_segmentation_decision():
    """Replay the out-of-scope question found in the successfully exported email PDF."""
    case = next(case for case in CASES if case["key"] == "email")
    evidence = build_evidence(case["description"], [])
    question = (
        "Will the system implement micro-segmentation to isolate email traffic "
        "from other network segments?"
    )
    assert not decision_topics(question, evidence)


def test_explicit_stakeholder_unknown_survives_without_a_registered_model_topic():
    """Machine-question filtering must not discard authoritative user decisions."""
    quote = "We have not decided whether laboratory booking is in scope."
    evidence = build_evidence(quote, [])
    assert deduplicate_decisions([quote], evidence) == [quote]


def test_configure_permission_has_a_literal_wifi_actor_despite_analysis_qualifier(
    analysis, complete_document
):
    """Keep the literal configure-role despite an extra analysis organization qualifier."""
    from cybersrs.scenario_projection import scenario_inventory

    case = next(case for case in CASES if case["key"] == "wifi")
    evidence = build_evidence(case["description"], [])
    units = [
        unit
        for fact in evidence
        for unit in source_obligations(fact)
        if unit.section == "functional"
    ]
    template = complete_document.functional.requirements[0].model_dump()
    rows = [
        template
        | {"id": f"FR-{index:03d}", "statement": unit.statement, "evidence_ids": [unit.evidence_id]}
        for index, unit in enumerate(units, 1)
    ]
    interpreted = analysis.model_copy(
        update={
            "stakeholders": [
                "university network administrator",
                "students",
                "faculty",
                "staff",
                "guests",
            ]
        }
    )
    inventory = scenario_inventory({"functional": {"requirements": rows}}, evidence, interpreted)
    assert inventory["actor_options"] == {
        f"FR-{index:03d}": ["Network administrators"] for index in range(9, 13)
    }


def test_timestamped_and_actor_aliases_cannot_confirm_unknown_audit_fields():
    """Replay the actual firewall row that used timestamped/identifier variants."""
    outcome = (
        "The audit log contains a timestamped entry with the action type, "
        "target resource, and actor identifier"
    )
    source = build_evidence(
        "Maintain audit logs of firewall policy changes and administrative actions.", []
    )
    assert set(unsupported_observed_fields(outcome, source)) == {
        "timestamp",
        "actor identifier",
        "action type",
        "target resource",
    }


def test_explicit_audit_fields_accept_their_equivalent_aliases():
    """Source-confirmed timestamps and actor IDs remain valid rather than being erased."""
    source = build_evidence(
        "Audit logs contain timestamps, actor IDs, action types and target resources.", []
    )
    assert not unsupported_observed_fields(
        "A timestamped entry contains an actor identifier, action type and target resource", source
    )
