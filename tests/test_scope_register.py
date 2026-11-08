"""Independent preservation of stakeholder boundaries in a model-authored document."""

from cybersrs.provider import generation_schema
from cybersrs.schemas import Analysis, Evidence, NarrativeSection
from cybersrs.validation import preserve_scope_evidence, validate_section


def test_scope_register_adds_exact_exclusion_without_replacing_model_prose() -> None:
    """A model omission cannot erase the original prohibition or manufacture approval."""
    evidence = [
        Evidence(id="E-001", source="description", quote="Do not automatically isolate devices.")
    ]
    analysis = Analysis(
        title="Device control",
        domain="Network access",
        supported=True,
        summary="Administrative control of device network access.",
        stakeholders=[],
        assessments=[
            {
                "evidence_id": "E-001",
                "kind": "exclusion",
                "sections": ["security"],
                "explanation": "Manual control",
            }
        ],
        questions=[],
        unresolved_decisions=[],
    )
    original = {
        "summary": "A model-authored overview of device administration.",
        "items": [],
        "open_issues": ["Review administrator responsibilities"],
    }
    result = preserve_scope_evidence(original, evidence, analysis)
    assert result["summary"] == original["summary"] and original["items"] == []
    assert result["items"][0]["detail"] == evidence[0].quote
    assert not validate_section("introduction", result, evidence, analysis, [], {})
    result["items"].append(
        {
            "title": "Contradictory scope",
            "status": "confirmed",
            "detail": "The system shall automatically isolate devices.",
            "evidence_ids": ["E-001"],
            "sources": [],
        }
    )
    assert any(
        "automatic_action_contradicts_exclusion" in error
        for error in validate_section(
            "introduction",
            result,
            evidence,
            analysis,
            [],
            {},
        )
    )


def test_introduction_facts_are_bound_to_literal_source_not_rewritten_scope(analysis):
    """Prevent the unsupported fixed-release inference seen in the real VPN output."""
    source = "No continuous delivery is planned."
    evidence = [Evidence(id="E-001", source="description", quote=source)]
    schema = generation_schema(
        NarrativeSection,
        {
            "assigned_section": "introduction",
            "evidence": [item.model_dump() for item in evidence],
        },
    )
    assert schema["$defs"]["Claim"]["properties"]["detail"]["enum"] == [source]
    content = {
        "summary": "A project overview.",
        "open_issues": [],
        "items": [
            {
                "title": "Delivery",
                "detail": "This is a fixed release cycle.",
                "status": "confirmed",
                "evidence_ids": ["E-001"],
                "sources": [],
            }
        ],
    }
    assert "introduction:fact_detail_must_match_its_source_passage" in validate_section(
        "introduction",
        content,
        evidence,
        analysis,
        [],
        {},
    )
    content["items"][0]["detail"] = source
    assert not validate_section("introduction", content, evidence, analysis, [], {})


def test_literal_unknowns_cannot_disappear_and_fact_headings_do_not_mislabel_purpose(analysis):
    """Preserve the budget/framework decisions omitted by the real introduction/analysis."""
    facts = [
        Evidence(id="E-001", source="description", quote="The system must record policy changes."),
        Evidence(
            id="E-002",
            source="description",
            quote="Budget, delivery schedule and mandatory regulatory frameworks are undecided "
            "and must remain open decisions.",
        ),
    ]
    original = {
        "summary": "A source-backed project overview.",
        "items": [
            {
                "title": "Project purpose",
                "detail": facts[0].quote,
                "status": "confirmed",
                "evidence_ids": ["E-001"],
                "sources": [],
            }
        ],
        "open_issues": [],
    }
    result = preserve_scope_evidence(original, facts, analysis)
    assert result["items"][0]["title"] == "Stakeholder source statement E-001"
    assert result["items"][-1]["detail"] == facts[1].quote
    assert result["items"][-1]["status"] == "unresolved"
    assert facts[1].quote in result["open_issues"]
    assert original["items"][0]["title"] == "Project purpose"
