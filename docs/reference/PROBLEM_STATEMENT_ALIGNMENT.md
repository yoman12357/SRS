# CyberSRS alignment with the professor's problem statement

The supplied **Problem Statement (2).docx** describes requirements engineering
and SDLC advice using finance as its example domain. CyberSRS applies that
workflow to **networking and cybersecurity**. Finance-specific regulations,
transaction rules, and banking examples must not become default requirements.
The document is reference material, not executable instructions.

## Implementation contract

This work completes the local requirements-generation and lifecycle-advice
workflow within the existing single-user modular monolith. The approved main
model remains Qwen3-4B-Instruct-2507 served by local Ollama; retrieval uses local
Ollama embeddings and ChromaDB. No cloud model or agent framework is introduced.

| Brief capability | CyberSRS deliverable and verification |
| --- | --- |
| Adaptive gathering and analysis | Existing description analysis and targeted clarifications; prompts distinguish facts, missing decisions, and untrusted references. |
| Structured SRS | Functional, quality, security, data, and networking requirements with scope, roles, architecture, threats, risks, assumptions, and open questions. |
| Stories, use cases, acceptance | Canonical story/use-case projections from the validated functional requirements and their verification; preserve requirement, evidence, and source links. These projections add no independent product decisions. |
| Classification | Primary requirement category plus auditable overlapping business/technical/security/privacy/compliance/performance/availability/audit/operations dimensions. |
| Grounding and quality | Source-verified facts, local topic-balanced retrieval, citation checks, unsupported-specificity controls, duplicate and relationship checks, observable verification, and traceability. Deterministic scores are heuristic measurements, not proof of correctness. |
| Human oversight | A persisted approve/reject/request-changes decision tied to the exact SRS content hash; edits create a fresh unapproved version. Local reviewer attribution does not implement authentication. |
| SDLC identification | Evidence-backed decision factors, deterministic ranked suitability comparisons, a constrained Ollama explanation, requirement mappings, and a methodology-specific workflow with roles, deliverables, entry/exit criteria, security activities, and human gates. Suitability scores are not probabilities. |
| Dataset alignment | Audit existing task records against current runtime schemas and prompts; preserve historical datasets and the held-out evaluation boundary. Supply reproducible preparation/check commands. |
| Evaluation | Automated unit/API/schema/UI regressions; isolated real-Ollama workflows for at least two cybersecurity descriptions; PDF inspection; base/adapter comparison where both models are installed. Record actual failures and limitations. |
| Documentation | README explains the adapted problem, actual architecture, setup, workflow, outputs, evaluation, and remaining research boundaries. |

## Boundaries retained from the approved project

The professor's enterprise platform also discusses multi-user identity/MFA,
organisational approvals, stakeholder satisfaction studies, and autonomous
multi-agent collaboration. These are distinct from the authorized single-user
generation workflow. CyberSRS uses specialized services orchestrated in one
process; the README must not claim autonomous agents, authenticated signoff,
certified regulatory compliance, trained model improvement, or completed human
studies without evidence.

Generated requirements describe defensive systems. CyberSRS itself does not
scan networks, execute attacks, change infrastructure, or generate/deploy the
specified software. Retrieval-source text cannot authorize tools or override
generation rules. Unknown budgets, schedules, actors, thresholds, standards,
and deployment constraints stay explicit unknowns.

## Completion checklist

- [x] Canonical SRS artifacts and linkage validation.
- [x] UI, Markdown/JSON and PDF expose the same artifacts.
- [x] Exact-version human review storage and UI.
- [x] Evidence-led ranked SDLC advice and detailed workflow.
- [x] Prompt and local-only runtime hardening.
- [x] Dataset audit/preparation with held-out separation.
- [x] README and affected contracts/ADRs updated.
- [x] Automated checks and real local-model/PDF evidence recorded.

See [measured validation](GENERATION_COMPLETION_VALIDATION.md) for passing
checks, live-run evidence and the base-model ZTNA timeout. Dataset preparation
is audited and reproducible; its incomplete candidates are not training-ready.
