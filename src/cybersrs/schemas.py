"""Strict canonical contracts shared by specialist agents, storage and exports."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

SectionName = Literal[
    "introduction",
    "functional",
    "nonfunctional",
    "security",
    "data",
    "network",
    "compliance",
    "architecture",
    "threats",
    "risks",
    "scenarios",
    "verification",
    "glossary",
    "sdlc",
]
RequirementSection = Literal["functional", "nonfunctional", "security", "data", "network"]
Dimension = Literal[
    "business",
    "technical",
    "security",
    "privacy",
    "compliance",
    "performance",
    "availability",
    "auditability",
    "operations",
    "usability",
    "data",
    "integration",
]


class StrictModel(BaseModel):
    """Disallow unexpected model-authored fields instead of silently dropping them."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Evidence(StrictModel):
    """An exact immutable input passage, distinct from retrieved advisory knowledge."""

    id: str
    source: str
    quote: str = Field(min_length=1)
    context: str = ""


class EvidenceAssessment(StrictModel):
    """Agent interpretation of one original passage; never a replacement for it."""

    evidence_id: str
    kind: Literal["requirement", "constraint", "exclusion", "context", "uncertain", "conflict"]
    sections: list[SectionName]
    explanation: str = Field(min_length=1)


class Question(StrictModel):
    """Adaptive stakeholder question associated with a specific missing decision."""

    id: str
    question: str = Field(min_length=8)
    why_needed: str = Field(min_length=8)
    critical: bool
    evidence_ids: list[str]


class Analysis(StrictModel):
    """Validated analysis and targeted questions over all original evidence."""

    title: str = Field(min_length=3)
    domain: str = Field(min_length=3)
    supported: bool
    summary: str = Field(min_length=10)
    stakeholders: list[str]
    assessments: list[EvidenceAssessment]
    questions: list[Question]
    unresolved_decisions: list[str]


class Answer(StrictModel):
    """Exact stakeholder response; skips remain explicit unknowns."""

    question_id: str
    text: str = Field(max_length=12000)
    skipped: bool = False
    question_text: str = ""


class SourceChunk(StrictModel):
    """A retrieved chunk with full end-to-end provenance."""

    id: str
    source_document_id: str
    chunk_index: int = Field(ge=0)
    page_or_section: str
    relevance_score: float = Field(ge=0, le=1)
    text: str
    title: str
    sha256: str


class Citation(StrictModel):
    """Literal support excerpt from an available chunk; applicability needs review."""

    chunk_id: str
    quote: str = Field(min_length=12)


class Claim(StrictModel):
    """Narrative assertion with its basis and explicit proposal status."""

    title: str = Field(min_length=2)
    detail: str = Field(min_length=1)
    status: Literal["confirmed", "proposed", "unresolved"]
    evidence_ids: list[str]
    sources: list[Citation]
    requirement_ids: list[str] = Field(default_factory=list)


class NarrativeSection(StrictModel):
    """Introduction, architecture or glossary authored by its specialist."""

    summary: str = Field(min_length=10)
    items: list[Claim]
    open_issues: list[str]


class ArchitectureComponent(Claim):
    """A proposed logical building block with a concrete responsibility."""

    component_name: str = ""
    responsibility: str = ""


class ArchitectureFlow(Claim):
    """A directed interaction or data movement between named logical components."""

    from_component: str = ""
    to_component: str = ""
    data_or_action: str = ""


class ArchitectureBoundary(Claim):
    """An enforced crossing between untrusted and trusted logical components."""

    untrusted_component: str = ""
    trusted_component: str = ""
    enforcement: str = ""


class ArchitectureSection(NarrativeSection):
    """Logical components, flows and trust boundaries linked to frozen requirements."""

    items: list[ArchitectureComponent]
    data_flows: list[ArchitectureFlow] = Field(default_factory=list)
    trust_boundaries: list[ArchitectureBoundary] = Field(default_factory=list)


class ArchitectureComponents(StrictModel):
    """First architecture stage: named logical nodes covering the required responsibilities."""

    summary: str = Field(min_length=10)
    items: list[ArchitectureComponent] = Field(min_length=1)
    open_issues: list[str]


class ArchitectureInteractions(StrictModel):
    """Second architecture stage: flows and boundaries using the frozen component vocabulary."""

    data_flows: list[ArchitectureFlow] = Field(min_length=1)
    trust_boundaries: list[ArchitectureBoundary] = Field(min_length=1)
    open_issues: list[str]


class ArchitectureOwnerLink(StrictModel):
    """Assign an existing source obligation to a proposed implementation component."""

    requirement_id: str
    component_name: str


class ArchitectureOwnership(StrictModel):
    """Complete missing component ownership without rewriting validated component proposals."""

    links: list[ArchitectureOwnerLink] = Field(min_length=1)


class ArchitectureComponentPlacement(StrictModel):
    """Model-chosen logical grouping of existing canonical responsibilities."""

    component_name: str = Field(min_length=3)
    requirement_ids: list[str] = Field(min_length=1)


class ArchitectureLayoutComponents(StrictModel):
    """Proposed implementation layout without free-text product commitments."""

    components: list[ArchitectureComponentPlacement] = Field(min_length=1)


class ArchitectureFlowPlacement(StrictModel):
    """A proposed directed interaction carrying only canonical source behavior."""

    from_component: str
    to_component: str
    requirement_ids: list[str] = Field(min_length=1)


class ArchitectureBoundaryPlacement(StrictModel):
    """Model-chosen trust-domain crossing with canonical enforcement responsibilities."""

    untrusted_component: str
    trusted_component: str
    requirement_ids: list[str] = Field(min_length=1)


class ArchitectureLayoutInteractions(StrictModel):
    """Source-backed interaction and trust-boundary layout decisions."""

    data_flows: list[ArchitectureFlowPlacement] = Field(min_length=1)
    trust_boundaries: list[ArchitectureBoundaryPlacement] = Field(min_length=1)


class ArchitectureInternalInteractions(StrictModel):
    """Optional internal interactions supplement the separately compiled mandatory source paths."""

    data_flows: list[ArchitectureFlowPlacement] = Field(default_factory=list)
    trust_boundaries: list[ArchitectureBoundaryPlacement] = Field(default_factory=list)


class AcceptanceCriterion(StrictModel):
    """Observable, model-authored pass/fail test for a requirement."""

    given: str = Field(min_length=8)
    when: str = Field(min_length=8)
    then: str = Field(min_length=12)
    method: Literal["test", "inspection", "analysis", "demonstration"]
    observable_evidence: str = Field(min_length=10)


class SourceIntroductionPlan(StrictModel):
    """Organize every authoritative fact without paraphrasing its scope or quantities."""

    evidence_order: list[str]


class Requirement(StrictModel):
    """Canonical requirement; the orchestrator, not the LLM, assigns its ID."""

    id: str = ""
    title: str = Field(min_length=3)
    statement: str = Field(min_length=20)
    rationale: str = Field(min_length=10)
    priority: Literal["must", "should", "could"]
    dimensions: list[Dimension] = Field(min_length=1)
    basis: Literal["explicit", "derived", "proposed"]
    evidence_ids: list[str]
    sources: list[Citation]
    dependencies: list[str]
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)
    unresolved_decisions: list[str]


class AcceptanceTestRepair(StrictModel):
    """One model-authored supplementary test linked to a source-backed requirement."""

    requirement_id: str
    acceptance_criterion: AcceptanceCriterion


class RequirementRationaleRepair(StrictModel):
    """A model-authored rationale correction that cannot rewrite valid behavior or tests."""

    rationale: str = Field(min_length=12)


class ObservableEvidenceRepair(StrictModel):
    """A witness-only correction cannot rewrite its validated action or expected behavior."""

    observable_evidence: str = Field(
        min_length=10, pattern=r"^(Capture|Record|Compare|Inspect|Query|Observe|Collect|Export) .+$"
    )


class RelatedAcceptanceCriteria(StrictModel):
    """Preserve additional authored verification when another section shares a control."""

    requirement_id: str
    title: str
    rationale: str
    dimensions: list[Dimension]
    evidence_ids: list[str]
    sources: list[Citation]
    acceptance_criteria: list[AcceptanceCriterion]
    unresolved_decisions: list[str] = Field(default_factory=list)


class RequirementsSection(StrictModel):
    """Complete requirements for one category; no arbitrary count quotas."""

    applicability_reason: str = Field(min_length=8)
    requirements: list[Requirement]
    related_requirement_ids: list[str] = Field(default_factory=list)
    related_acceptance_criteria: list[RelatedAcceptanceCriteria] = Field(default_factory=list)


class ComplianceMapping(StrictModel):
    """Reviewable applicability/control mapping, never a legal certification."""

    id: str = ""
    framework_or_policy: str
    control_or_section: str
    applicability: Literal["confirmed", "advisory", "pending"]
    rationale: str = Field(min_length=12)
    requirement_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str]
    sources: list[Citation]
    human_review_required: Literal[True] = True


class ComplianceSection(StrictModel):
    """Explicit control matrix and unresolved jurisdiction/framework decisions."""

    mappings: list[ComplianceMapping]
    open_decisions: list[str]


class Threat(StrictModel):
    """Defensive threat scenario linked to actual requirement controls."""

    id: str = ""
    asset: str
    actor: str
    scenario: str = Field(min_length=20)
    impact: str = Field(min_length=10)
    control_requirement_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str]
    sources: list[Citation]
    residual_risk: str = Field(min_length=10)


class ThreatSection(StrictModel):
    """Threat-model specialist output."""

    threats: list[Threat]
    assumptions: list[str]


class Risk(StrictModel):
    """Project-specific risk rationale and a proposed mitigation for human review."""

    id: str = ""
    description: str = Field(min_length=15)
    likelihood: Literal["low", "medium", "high", "unknown"]
    impact: Literal["low", "medium", "high", "unknown"]
    rationale: str = Field(min_length=12)
    mitigation: str = Field(min_length=12)
    requirement_ids: list[str]
    evidence_ids: list[str]
    owner: str


class RiskSection(StrictModel):
    """Risk specialist output; ratings are advisory, never calibrated probabilities."""

    risks: list[Risk]
    open_issues: list[str]


class Scenario(StrictModel):
    """Linked story/use case preserving actor, success and exceptional behavior."""

    id: str = ""
    actor: str
    goal: str
    story: str = Field(min_length=20)
    preconditions: list[str]
    steps: list[str] = Field(min_length=1)
    success_outcome: str = Field(min_length=10)
    alternate_flows: list[str]
    requirement_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str]
    unresolved_decisions: list[str]


class ScenarioSection(StrictModel):
    """Stories and use cases linked to existing canonical requirements."""

    scenarios: list[Scenario]
    open_issues: list[str]


class ScenarioActorSelection(StrictModel):
    """Select a literal source role for one canonical actor-visible requirement."""

    requirement_id: str
    actor: str


class SourceCandidatePlan(StrictModel):
    """Select and order applicable source-derived advisory candidates."""

    candidate_keys: list[str]


class ScenarioProjectionPlan(StrictModel):
    """Choose source actors and denied variants without paraphrasing product behavior."""

    actors: list[ScenarioActorSelection]
    alternate_criterion_keys: list[str]


class Verification(StrictModel):
    """Test recommendation tied to existing authored acceptance criteria."""

    id: str = ""
    requirement_ids: list[str] = Field(min_length=1)
    procedure: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=15)
    evidence_to_record: str = Field(min_length=12)
    test_type: Literal["positive", "negative", "boundary", "inspection", "analysis"]


class VerificationSection(StrictModel):
    """Verification specialist output covering every canonical requirement."""

    tests: list[Verification]
    limitations: list[str]


class CriterionVerificationChoice(StrictModel):
    """Classify one existing criterion without re-authoring its behavior or evidence."""

    criterion_key: str
    test_type: Literal["positive", "negative", "boundary", "inspection", "analysis"]


class VerificationPlan(StrictModel):
    """Internal model selections over a complete frozen criterion inventory."""

    choices: list[CriterionVerificationChoice]


class SDLCFactor(StrictModel):
    """Evidence-backed deterministic decision factor."""

    name: str
    value: str
    evidence_ids: list[str]
    basis: Literal["explicit", "derived"] = "explicit"
    rationale: str = ""


class LifecycleWorkGroup(StrictModel):
    """Group canonical obligations without free-text product tasks."""

    requirement_ids: list[str] = Field(min_length=1)


class LifecycleWorkPlan(StrictModel):
    """Local-model explanation and work grouping for the ranked methodology."""

    justification: str = Field(min_length=30)
    work_groups: list[LifecycleWorkGroup]


class SDLCCandidate(StrictModel):
    """Versioned rule suitability points, not a probability."""

    model: str
    score: int
    reasons: list[str]


class SDLCPhase(StrictModel):
    """Methodology-specific project workflow stage and human validation gate."""

    name: str
    phase_type: (
        Literal[
            "planning",
            "design",
            "implementation",
            "verification",
            "release",
            "iteration",
            "operations",
        ]
        | None
    ) = None
    activities: list[str] = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    deliverables: list[str] = Field(min_length=1)
    entry_criteria: list[str] = Field(min_length=1)
    exit_criteria: list[str] = Field(min_length=1)
    security_checks: list[str] = Field(min_length=1)
    human_approval: str = Field(min_length=10)
    requirement_ids: list[str]


class SDLCVerificationPair(StrictModel):
    """A recommended early test plan and its later corresponding verification stage."""

    development_phase: str = Field(min_length=3)
    verification_phase: str = Field(min_length=3)
    test_scope: Literal["unit", "integration", "system", "acceptance"]
    test_plan_deliverable: str = Field(min_length=8)
    requirement_ids: list[str] = Field(min_length=1)


class SDLCWorkflow(StrictModel):
    """Frozen methodology workflow inventory, before verification relationships."""

    selected_model: str
    justification: str = Field(min_length=30)
    tradeoffs: list[str] = Field(min_length=1)
    phases: list[SDLCPhase] = Field(min_length=3)
    unknown_factors: list[str]


class SDLCSection(SDLCWorkflow):
    """Constrained explanation and complete workflow for the deterministic winner."""

    verification_pairs: list[SDLCVerificationPair] = Field(default_factory=list)


class SDLCVerificationLinks(StrictModel):
    """Relationships constrained to a previously validated workflow inventory."""

    verification_pairs: list[SDLCVerificationPair] = Field(min_length=1)


class AgilePreparationPhase(SDLCPhase):
    """Source refinement and preparation before recurring delivery starts."""

    phase_type: Literal["planning"] = "planning"


class AgileReleasePhase(SDLCPhase):
    """A proposed release/handoff gate after reviewed delivery evidence."""

    phase_type: Literal["release"] = "release"


class AgileIterationPhase(StrictModel):
    """Distinct model-authored activities prevent relabelling a test-only phase as iteration."""

    name: str = Field(min_length=3)
    planning_actions: list[str] = Field(min_length=1)
    implementation_actions: list[
        Annotated[str, Field(pattern=r"^(?:Implement|Develop|Build|Deliver|Integrate)\b.+$")]
    ] = Field(min_length=1)
    verification_actions: list[
        Annotated[str, Field(pattern=r"^(?:Test|Verify|Validate|Execute|Inspect)\b.+$")]
    ] = Field(min_length=1)
    feedback_actions: list[
        Annotated[str, Field(pattern=r"^(?:Collect|Review|Discuss|Demonstrate)\b.+$")]
    ] = Field(min_length=1)
    next_iteration_actions: list[
        Annotated[
            str,
            Field(pattern=r"^(?:Update|Refine|Reprioritize|Return)\b.+$"),
        ]
    ] = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    deliverables: list[str] = Field(min_length=1)
    entry_criteria: list[str] = Field(min_length=1)
    exit_criteria: list[str] = Field(min_length=1)
    security_checks: list[str] = Field(min_length=1)
    human_approval: str = Field(min_length=10)
    requirement_ids: list[str]


class AgileLifecycle(StrictModel):
    """Internal cycle response composed into the unchanged public SDLC section."""

    selected_model: Literal["Agile"] = "Agile"
    justification: str = Field(min_length=30)
    tradeoffs: list[str] = Field(min_length=1)
    preparation: AgilePreparationPhase
    iteration: AgileIterationPhase
    release: AgileReleasePhase
    unknown_factors: list[str]


class ChatResponse(StrictModel):
    """Validated general cybersecurity answer with scoped local citations."""

    answer: str = Field(min_length=1)
    sources: list[Citation]


class Finding(StrictModel):
    """Reviewable validation result; safe codes distinguish failures from warnings."""

    code: str
    severity: Literal["error", "warning"]
    section: str
    item_id: str
    message: str


class QualityReport(StrictModel):
    """Deterministic checks, explicitly distinct from semantic/human approval."""

    validation_policy_version: str = ""
    status: Literal["invalid", "needs_review"]
    checks_passed: int
    checks_total: int
    findings: list[Finding]
    evidence_coverage: dict[str, list[str]]
    traceability: list[dict[str, str | list[str]]]


class Document(StrictModel):
    """Canonical complete SRS. Renderers consume only this validated structure."""

    schema_version: Literal["1.0"] = "1.0"
    project_id: str
    title: str
    original_description: str
    evidence: list[Evidence]
    analysis: Analysis
    sources: list[SourceChunk]
    introduction: NarrativeSection
    functional: RequirementsSection
    nonfunctional: RequirementsSection
    security: RequirementsSection
    data: RequirementsSection
    network: RequirementsSection
    compliance: ComplianceSection
    architecture: ArchitectureSection
    threats: ThreatSection
    risks: RiskSection
    scenarios: ScenarioSection
    verification: VerificationSection
    glossary: NarrativeSection
    sdlc: SDLCSection
    sdlc_policy_version: str
    sdlc_prompt_version: str = ""
    category_metadata_version: str = ""
    verification_projection_version: str = ""
    introduction_projection_version: str = ""
    scenario_projection_version: str = ""
    sdlc_factors: list[SDLCFactor]
    sdlc_candidates: list[SDLCCandidate]
    model_name: str
    requested_model_name: str = ""
    models_used: list[str] = Field(default_factory=list)
    section_models: dict[str, list[str]] = Field(default_factory=dict)
    prompt_version: str
    input_fingerprint: str = ""


SECTION_SCHEMAS: dict[str, type[StrictModel]] = {
    "introduction": NarrativeSection,
    "functional": RequirementsSection,
    "nonfunctional": RequirementsSection,
    "security": RequirementsSection,
    "data": RequirementsSection,
    "network": RequirementsSection,
    "compliance": ComplianceSection,
    "architecture": ArchitectureSection,
    "threats": ThreatSection,
    "risks": RiskSection,
    "scenarios": ScenarioSection,
    "verification": VerificationSection,
    "glossary": NarrativeSection,
    "sdlc": SDLCSection,
}
REQUIREMENT_PREFIXES = {
    "functional": "FR",
    "nonfunctional": "NFR",
    "security": "SEC",
    "data": "DR",
    "network": "NET",
}
