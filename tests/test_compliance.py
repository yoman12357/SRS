"""Compliance mappings require evidence rather than domain-default regulations."""

from cybersrs.policy_applicability import policy_adoption_is_explicit
from cybersrs.validation import validate_section


def test_unconfirmed_framework_cannot_be_mandatory(complete_document) -> None:
    """A cybersecurity project does not automatically establish GDPR or financial regulations."""
    content = {
        "mappings": [
            {
                "id": "CMP-001",
                "framework_or_policy": "GDPR",
                "control_or_section": "Article 32",
                "applicability": "confirmed",
                "rationale": "A model inferred regulatory applicability.",
                "requirement_ids": ["SEC-001"],
                "evidence_ids": ["E-002"],
                "sources": [],
                "human_review_required": True,
            }
        ],
        "open_decisions": [],
    }
    issues = validate_section(
        "compliance",
        content,
        complete_document.evidence,
        complete_document.analysis,
        [],
        complete_document.model_dump(),
    )
    assert any("unconfirmed_framework_applicability" in issue for issue in issues)
    assert any("missing_compliance_source" in issue for issue in issues)


def test_unknown_or_denied_policy_is_not_adoption() -> None:
    """A framework mention cannot become a mandatory compliance decision by itself."""
    assert not policy_adoption_is_explicit("Mandatory regulatory frameworks are undecided.")
    assert not policy_adoption_is_explicit("The NIST framework is not required.")
    assert policy_adoption_is_explicit("The system must comply with NIST SP 800-53.")
