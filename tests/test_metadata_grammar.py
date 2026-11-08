"""Grammar-boundary regression for deterministic project-context routing."""

from cybersrs.provider import generation_schema
from cybersrs.schemas import Analysis


def test_context_metadata_grammar_cannot_invent_runtime_features() -> None:
    """Bind known planning/context hints to context-only output classifications."""
    schema = generation_schema(
        Analysis,
        {
            "evidence": [{"id": "E-001"}, {"id": "E-002"}],
            "project_context_evidence_ids": ["E-001"],
        },
    )
    branches = schema["$defs"]["EvidenceAssessment"]["anyOf"]
    metadata = branches[0]["properties"]
    assert metadata["evidence_id"]["enum"] == ["E-001"]
    assert "requirement" not in metadata["kind"]["enum"]
    assert metadata["sections"]["items"]["enum"] == ["introduction", "sdlc"]
    assert branches[1]["properties"]["evidence_id"]["enum"] == ["E-002"]
