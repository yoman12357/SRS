# CyberSRS Sequential Agents — product contract

The user requests a new, independent Desktop project. Preserve the original.
Reuse existing Qwen adapters, datasets and local knowledge. The active design
supersedes the historical grouped-generation architecture in docs/reference.

A person enters an informal cybersecurity/networking description. Local Ollama
analyses exact evidence and asks adaptive questions only when information is
missing or conflicting. A central orchestrator runs one specialist per SRS
section, sequentially, using the configured Qwen model. Each agent reads validated
shared context and produces schema-validated JSON. Store intermediate sections
and provenance in SQLite. Assemble the canonical document, validate relationships
and coverage, derive linked artifacts, recommend an evidence-backed SDLC, and
render a PDF from exactly the stored document.

Required functionality: project CRUD/resume, clarification/skip, local reference
uploads, RAG with citations, agent progress/cancel/retry, section editing and
regeneration, immutable versions, exact-content human decisions, JSON/Markdown/PDF
export, general cybersecurity conversation, adapter/base evaluation, dataset
provenance, and reproducible setup. Never claim model output is human-approved.

Correctness means preserving explicit user constraints and exclusions, exposing
unknowns and contradictions, avoiding invented quantities/technologies/regulations,
retaining testable acceptance criteria, no dangling references, and complete
traceability. Validation is evidence and heuristics, not formal correctness proof.

The adopted scope of the professor's brief is in PROBLEM_STATEMENT_ALIGNMENT.md.
Its financial examples are adapted to cybersecurity. Do not invent banking compliance. Enterprise
identity/MFA and human satisfaction studies remain outside the local single-user
scope. Agents have no execution, network-management or attack tools.
