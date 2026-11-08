# API contract (v1)

All routes use /api/v1. Errors return {detail:{code,message}}. JSON is validated.
User content is stored locally; safe diagnostics exclude prompts/raw model output.

Under ADR-0054, version detail/JSON exports additionally return `presentation`
outside immutable `content`: profile, title, and numbered report sections. Each
section has number, title, paragraphs, bullets, tables and canonical requirements.
The presentation is derived without inference and does not change content hashes.
PDF and Markdown exports default to the concise IEEE 830-1998 report; optional
`?detail=full` returns the exhaustive supporting report. Both profiles preserve
draft/approval status and canonical requirement IDs. JSON retains all canonical
fields regardless of detail. Export audit events record the chosen detail.

| Method/path | Behavior |
| --- | --- |
| GET /health | Local runtime/model readiness and knowledge counts |
| GET,POST /projects | List/create name and description |
| GET,PATCH,DELETE /projects/{id} | Detail/update/delete project and associated data |
| POST /projects/{id}/analyse | Start background input analysis run |
| POST /projects/{id}/answers | Store question IDs, answer text and skipped flags; reanalyse |
| POST /projects/{id}/clarifications | Confirm the displayed analysis and prepare its clarification questions |
| POST /projects/{id}/generate | Start sequential generation; requires analysed input |
| GET /runs/{id} | Status, agent events, validated checkpoints, safe error |
| GET /projects/{id}/runs | Recent run summaries to restore progress after reload |
| POST /runs/{id}/cancel | Idempotent cooperative cancellation |
| POST /runs/{id}/retry | Resume a terminal failed/cancelled/interrupted run using revalidated checkpoints and identical inputs |
| GET /projects/{id}/versions | Immutable version summaries |
| GET /projects/{id}/versions/{version} | Exact canonical document, quality and hash |
| PUT /projects/{id}/versions/{version}/sections/{section} | Validate edited section and create a successor |
| POST /projects/{id}/versions/{version}/regenerate/{section} | Regenerate selected section plus affected dependent artifacts |
| POST /projects/{id}/versions/{version}/reviews | Explicit approve/reject/request_changes with reviewer, comment and exact content_hash |
| GET /projects/{id}/versions/{version}/reviews | Review history for that hash |
| GET /projects/{id}/versions/{version}/export/{format} | JSON, Markdown or PDF; mark draft unless valid and human-approved |
| GET,POST /projects/{id}/documents | List/upload PDF, text, Markdown or CSV reference |
| DELETE /projects/{id}/documents/{document} | Remove reference and its private index chunks |
| POST /chat | Validated cybersecurity answer with local RAG citations; no implicit project creation |
| GET /projects/{id}/audit | Explicit private JSON audit download with source revisions, model requests/responses, decisions and exact export artifacts |

The interactive workflow calls `POST /clarifications` on the project after the
user checks its analysis. It returns `{review_token, questions}` bound to the
current source inputs and exact analysis. Questions come from validated analysis
and source-stated open decisions. The user can leave any answer blank.

The interactive `POST /generate` accepts `{review_token, answers}`. Answers use
the existing answer shape and belong to this reviewed question set. Stale review
tokens are rejected. The returned run owns any necessary answer analysis,
section generation and bounded automatic recovery under one wall-clock
budget, capped at 480 seconds. Human review and question time precede this
budget. The response and run-detail route include `budget_seconds`. Existing
bodyless generation and separate answer submission remain supported.

Under ADR-0017, the audit attachment includes project-scoped append-only events,
content hashes and timestamps. Source revisions include prior/new state; inference
records include exact requests, response envelopes and validation decisions.
Document export records retain SHA-256, canonical version hash and base64 bytes.
Ordinary run/project/version routes never include this private history. Deletion
of a project deletes its audit records. No historical audit is fabricated.
Standalone chat is ephemeral; project-scoped chat is audited. Audit records remain
local until project deletion and are not a tamper-proof ledger.

Creation accepts {name,description}. Answers accepts {answers:[{question_id,text,
skipped}]}. Section edit accepts {content,expected_content_hash}. Review accepts
{decision,reviewer,comment,content_hash}. Chat accepts {message,project_id?}.
Run status is queued/running/completed/failed/cancelled/interrupted. Only completed
generation produces a version; interrupted runs remain inspectable after restart.

Run `created_at`, `updated_at` and each event's `at` are UTC ISO timestamps.
The UI uses running/completed event timestamps for live and finished section
timers, and the terminal run timestamp to freeze interrupted work. `reused=true`
identifies a reused checkpoint, not a newly generated section. Completed section
events may include `repaired_source_ids` for bounded model-authored source-group
corrections; the canonical schema and approval behavior remain unchanged.
Completed section
`elapsed_seconds` includes retrieval and all corrective work. The configured
section timeout applies across the whole section, rather than restarting per
model call. Timing out is a failed run, never a successful truncated SRS.
The local streaming transport uses an absolute deadline, including silent socket
reads and model-lock waiting. Optional retrieval has its own bounded share of
that section budget. Completed analysis is shown separately from a completed SRS.

Version reads, exports and approval requests recompute quality under current
rules. Historical JSON content and its hash remain immutable. A currently invalid
version cannot be approved even if its validation report passed when generated.
Generated content records requested/actual model tags and section-level provenance;
base-Qwen corrections are distinct from adapter-only output.
Editing or regenerating architecture also rebuilds threats and risks from its
validated component/flow/boundary context. Public ArchitectureSection shape stays
the same; internal component and interaction drafting stages are recorded in run
provenance. An invalid historical prerequisite architecture must be regenerated
before dependent artifacts can consume it.

SDLCSection adds optional `verification_pairs` (default empty for historical
documents): development_phase, verification_phase, test_scope (unit, integration,
system or acceptance), test_plan_deliverable and requirement_ids. Current V-Model
generation/edit validation requires resolved forward phase links, an early
test-plan deliverable in the development phase, acceptance and technical pairings,
and canonical requirement coverage. This represents a recommended workflow; it
does not record executed tests or human approval.

Generation audit also records source-bound normalization: unsupported positive
architecture timing modifiers and unsupported explanatory denial-message copy may
be removed while retaining the original response, normalized fields and reason.
Source commitments, test actions and denial outcomes still pass the complete
validators. This is neither human approval nor a general semantic-correctness proof.
# V-model workflow metadata (SDLC generation 1.2)

Current quality reports additionally return `validation_policy_version`. This
identifies the source-guard policy used for recomputation; it does not change an
immutable SRS content hash or constitute human approval. Binding metadata, linked
criteria, quantified commitments and future approval gates receive source checks.

SDLC phases may include `phase_type`: planning, design, implementation,
verification, release, iteration or operations. Historical phases without this
field remain readable; newly validated V-model content requires phase types,
early named test/verification plans, implementation, and later verification.
Pairs reference exact planning/design deliverables and cover unit, integration,
system and acceptance. Test IDs alone cannot be plan deliverables. Canonical
documents include `sdlc_prompt_version` (empty for historical documents).
Retry revalidates predecessor checkpoints and rebuilds SDLC when this version
changes. No endpoint or human-approval semantics change.

# Reviewed failed-generation corrections

A requirement-section edit that changes only applicability wording, titles, rationale or category
metadata revalidates and versions that section without redrafting unchanged
canonical behavior. Behavior, source, unresolved-decision, dependency or authored-criterion changes retain dependency
regeneration. Linked views and the final quality/traceability report are rebuilt.

`POST /runs/{run_id}/retry` still accepts an empty body. Optional body:
`{section_edits: {sectionName: sectionObject}, expected_input_hash: string,
editor: "human" | "assistant"}`. Edits require the exact source run input hash,
unchanged current inputs, and a terminated `generate` run. Unknown sections or
invalid schemas are rejected. Corrections are source/link validated in the worker;
dependent sections rebuild from the first correction. No partial success or
approval is created. The editor defaults to human; it is a provenance label,
not an authenticated identity.

The existing version section `PUT` also accepts optional `editor` with the same
meaning. Private request checkpoints retain exact edits and labels; ordinary
progress continues to hide private checkpoints.

The section `PUT` may additionally supply `dependent_edits`, a map of fully
reviewed dependent section objects. Each must belong to that section's normal
regeneration set. These objects pass the same schema/source/link checks and
replace new model drafting for those dependencies within one atomic successor.
The parent `content` remains separate. Unknown or unrelated keys are rejected.
Verification edits also rebuild SDLC so test references cannot silently go stale.

Generation profile 1.27 bounds passage-authored linked tests to canonical targets
from that source. A linked-test repair preserves its target and valid sibling
tests. Policy source-grounding-1.2 additionally checks recognized post-subject
concurrency, invented load caps, message/availability/peer-authentication promises,
unnamed regulation claims and unsupported risk labels. Risk likelihood/impact stay
unknown without linked source assessments. These are selected guards, not proof of
entailment. Current reads may therefore reject an older immutable draft that
passed an earlier policy; its stored content/hash remain unchanged.

Canonical documents additionally record `category_metadata_version` (empty for
historical documents). The initial category-metadata policy binds explanations
to a factual coverage statement and indexes only actual canonical IDs. The agent
sees the complete compact inventory and can select relevant links missing from
initial routing; no new rows or tests are authored when no source gap exists.
Retries refresh valid empty legacy category checkpoints without redrafting
unchanged canonical behavior or revalidated downstream sections. Edits of older
versions preserve their older metadata-version provenance.

Category metadata 1.1 additionally requires links established by canonical
statement topics/dimensions, independent of generated titles or rationale.

SDLC generation 1.4 and source-grounding policy 1.3 require typed phases, actual
Agile build/test iteration with a feedback return path, no V-specific pairs in
non-V workflows, and explicit source delivery assignments or Proposed role labels.
Only SDLC and legacy empty metadata need refresh for these version changes;
other artifacts retain normal validation/dependency rules.

Text-generation provenance and private model-request audit metadata include
`correction_policy_version`. Policy bounded-corrective-history-1.0 retains all
diagnostics within bounded retries and supplies the last schema-valid rejected
candidate as untrusted context. The optional candidate may be omitted whole when
it exceeds context capacity; authoritative inputs are never silently truncated.
An isolated rationale error can use a typed rationale-only correction, followed
by full requirement validation, preserving all other fields. None of these
corrections records a human decision or changes historical content hashes.

Source-grounding 1.4 distinguishes source-stated storage/inspection of existing
logs from recognized assertions that the product creates additional event logs.
SDLC generation 1.5 uses a typed internal Agile cycle and preserves its authored
planning/build/test/feedback/backlog actions in the existing public phase shape.
The public document schema and V-Model path remain unchanged. All composed
content still passes ordinary source, responsibility, coverage and approval gates.

Generation 1.6 permits additional next-cycle refinements without requiring every
action to repeat a backlog keyword; the complete workflow still requires an
actual return path. Targeted repair provenance records `requirement_repair_version`
when applied. Field-local-repair-1.1 repairs independently rejected canonical
criteria before whole-row repair, using the same source-bound typed test path as
linked criteria, then revalidates the complete row/section. Transient test views
are not stored as additional requirements or duplicated criteria.

Automatic canonical documents may record `verification_projection_version`
(empty for historical or explicitly edited verification). The verification
specialist classifies a complete inventory of canonical and linked criteria;
public tests retain the authored GIVEN/WHEN/THEN/evidence text with presentation
labels. Duplicate, omitted, unknown or method-changing choices are rejected.
Current quality checks compare claimed automatic plans to the actual criteria.
Retries refresh legacy verification and its dependent SDLC while preserving valid
earlier artifacts and glossary. Explicit verification edits keep ordinary source
validation and their editor provenance; they do not claim automatic projection.

Verification projection 1.1 constrains observed positive/negative outcomes and
permits a boundary label only with an actual quantified edge. Source-grounding
1.7 retains the aggregate excluded-action gate while internal repair policy 1.3
completes only the actual missing action per request. Valid combined tests may
cover several actions. Explicit active-scanning mode and traffic evidence remain
distinct from automatic firewall modification and configuration-state evidence.

Automatic documents may additionally record `introduction_projection_version`.
The introduction agent organizes every source fact once; the public narrative
retains exact quotations, source decision status, and question context on response
titles. A document-purpose overview does not paraphrase product commitments.
Current quality checks compare a claimed view with exact source facts. Legacy
unchanged-input retries refresh introduction and dependent SDLC without redrafting
other validated sections. Explicit introduction edits retain their editor label
and do not claim automatic projection.

Narrative detail accepts a nonempty short exact introduction quotation (for example,
"Yes"). The independent validator retains the eight-character rule elsewhere
and rejects fabricated/nonmatching short facts. Copied question-context titles
remain source metadata, not newly asserted product quantities.

Repair policy 1.4 may request only `observable_evidence` when independent full-
criterion checks isolate that field as the sole defect. Other authored fields and
the target remain unchanged; the full row is validated again. Incoherent creation-
only deletion triggers remain errors, so a witness patch cannot hide that defect.
A typed missing-obligation draft can use the same bounded criterion recovery;
the complete source-completion gate still must pass. Private failure metadata
retains the actual candidate author and total attempted calls; ordinary error text
continues to exclude rejected content.


Private generation diagnostics now retain actual rejected model tags and total
failed-call counts across primary/base attempts. Source-grounding 1.10 / repair
1.5 additionally reject selected unstated permission-management details and new
audit-log classes. A recognized missing management obligation uses a source-derived
statement constraint, checked independently of the native decoder. Public endpoint
and requirement schemas remain compatible. These checks do not prove entailment.

Architecture source-backed-layout1.1 retains the existing public section schema.
Internal typed layout/owner choices are model-authored; exact canonical duties,
source metadata and necessary role/access-decision paths are server-composed.
Private stage provenance identifies every actual call and source_paths_compiled.
Quality policy1.12 rejects missing source endpoints, wrong-role requests/boundaries
and access-decision paths that bypass their implementation owner. Existing manual
edits and exact-content review endpoints remain available.


### Source-derived views (2026-10-28)

No routes changed. Canonical Document JSON adds optional
`scenario_projection_version` (empty for historical/manual views). Generated
scenarios are independently checked against final requirements/criteria; manual
scenario edits clear that marker. Requirement changes rebuild dependent views.
Private run provenance also records source-advisory and lifecycle compilation
versions, distinct from actual model selections and author tags. SDLC fields and
PDF/Markdown/JSON exports remain compatible. No generation records human approval.

### Source-obligation authoring (2026-10-29)

ADR-0056 leaves routes and public requirement/evidence schemas unchanged.
Recognizable compound source predicates are separate canonical requirements with
their original evidence IDs. The local model authors acceptance tests; statements
are source-compiled. Private stage provenance distinguishes
`source_obligations_version`, `compiled_source_statements`, `atomic_source_keys`
and actual output model tags. These markers do not imply human approval.
Generated open-decision strings may reference a canonical analysis question as
`Decision Q-<key> is TBD.`; the corresponding question retains source evidence.
Human-edited sections and exact-version reviews retain their existing contract.

The run profile additionally records `atomic_test_repair_limit`; it caps field-only
atomic-test corrections within `section_timeout_seconds`. Verification may record
private `verification_selection_version=source-keyed-types-1.0`. Its native keyed
classification object is projected into the existing public verification tests;
no route, request body or canonical review schema changes. All criterion keys are
required exactly once before projection. Shared-word overlap is no longer a
fallback source of generated clarification questions.

### Cyber assessments, SDLC evidence and report choice (2026-10-30)

ADR-0057 changes no route or generation request body. Optional backward-compatible
SDLCFactor fields are `basis` (`explicit` default, or `derived`) and `rationale`
(empty default for historical records). New policy `sequential-sdlc-2.0` records
source-backed suitability factors; missing delivery decisions remain unknown.
The internal decision includes `provisional` and `decision_status`; canonical
workflow tradeoffs retain the proposed-decision caveat. These scores are not
probabilities or human approval.

The existing presentation schema now includes appendices A (threat hypotheses),
B (risks), and C (SDLC ranking, factors and workflow). GET exports use the existing
default IEEE reader and `?detail=full` Normal report for PDF/Markdown; JSON always
remains canonical. The frontend remembers `standard`/`full` per project locally.
No server-side format field, version mutation or inference occurs on format switching.

Private advisory provenance records `source_advisory_version`,
`model_candidate_order`, `retained_source_candidates` and `composition`. Complete
applicable threat/risk inventories are retained even when the model orders only a
subset. Descriptions and treatments are deterministic source-linked planning
proposals, not model-discovered vulnerabilities. Historical content is not backfilled.

### PAM source predicate reliability (2026-10-30)

ADR-0058 changes no public route, request body or canonical section schema.
`source_obligations_version=source-obligations-1.1` and prompt version
`sequential-1.34` identify the expanded independent predicate compilation and
recording validation fix. Resume does not reuse incompatible prompt checkpoints.
The existing bounded correction policy and failed-run status remain truthful;
there is no unconditional success or automatic approval fallback.

### Backup/configuration validation (2026-10-30)

ADRs 0059-0060 change no public routes or canonical field schema. Source
obligations 1.2 recognize product It, define/initiate/submit/track and protected
backup/restore noun phrases. Prompt 1.37 includes operation-specific observation
guidance and dashboard correction context. New checks reject copied object
templates and known unconfirmed registry, universal metadata and session
persistence details. Display checks evaluate the observed clause separately
from its initiating condition. Existing source, schema and bounded retry gates
remain in force; generation never supplies human approval.

ADR-0061 adds source-obligations-1.3/prompt sequential-1.38 for independently
preserved certificate issuance approval and renewal predicates. There are no
route, request or public schema changes. Runtime certificate approval remains
separate from exact-version human SRS review.

ADR-0062/prompt sequential-1.39 improves automatic API test-field corrections.
Access-decision checks accept active denies/permits/rejects wording. Detection
guidance is per operation even when its parent paragraph mentions alerts.
Corrective text retains short-field bounds, excludes digits when absent from
source, and constrains enforce/detect results to decision/recognition predicates.
Full semantic validation remains mandatory. The existing local
CYBERSRS_ATOMIC_TEST_REPAIR_LIMIT is 3 within the unchanged 120-second section
deadline. Routes, public schemas, immutable hashes and review contracts are unchanged.

ADR-0063/source-obligations-1.4/prompt sequential-1.41 uses one observed-outcome
predicate contract for both criterion validation and field-local native repair.
Every functional verb recognized by the source parser must have a corresponding
outcome constraint; registration, rejection and identification are now explicit
source actions. This removes prompt/validator drift without creating deterministic
acceptance text or bypassing source, logging, implementation-detail or completeness
checks. Routes, request bodies, public schemas, version hashes and review semantics
remain unchanged.
