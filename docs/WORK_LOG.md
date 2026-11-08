# Work log

2026-10-27: Read repository governance/plans and original Problem Statement (2).
Created independent Desktop target. Copied existing datasets, adapter and source
knowledge; SHA-256 inventory is docs/reference/ASSET_MANIFEST.json. The existing
Ollama base, merged fine-tuned Qwen and nomic embedding tags are installed.
Wrote the new architecture, API contract, scope and acceptance gates before code.
Implementation and live-output verification remain in progress.

Implemented fresh Python package, environment, strict agent schemas, SQLite
repository, sequential orchestration with bounded repairs, cancellation and
checkpoint retry, local provider, isolated Chroma retrieval/upload, immutable
edits/regeneration, exact-hash reviews, evidence-led SDLC ranking, and section-wise
PDF/Markdown/JSON. Built a fresh React interface with the same core workflow,
reference uploads, review and export, plus startup/setup scripts.

Verified 789 copied asset hashes with scripts/audit_assets.py; 1,038 historical
JSONL records parse (519 in each of two task directories). No retraining or label
changes. Seed ingestion indexed 111 chunks across six local OWASP documents.

Latest automated checks: 37 backend tests pass; 7 UI tests pass; TypeScript and
production Vite build pass; Ruff and Prettier pass; npm audit reports zero issues.
Third-party FastAPI/Chroma deprecation warnings remain. UI landing page inspected
in the app browser at http://127.0.0.1:8010. No real-model PDF has passed inspection.

Real adapter attempts under data/evaluations/20261027-024710-finetuned exposed
incorrect classification, missing exclusions, paraphrased citations, omitted manual
administrator isolation, unrelated zero-trust controls assigned to user evidence,
and weak acceptance evidence. No attempt has produced a completed version.
Added native literal-citation grammar, evidence-first normative drafting,
source-mode/actor/exclusion checks, observable verification rules and targeted
completion/retry. Earlier schema/link-only acceptance was not sufficient semantic
evidence. ADR-0002 documents this correction.

An actual base-Qwen comparison run was started under
data/evaluations/20261027-030238-base. Continue from current authoritative run/process
state before launching additional inference. Remaining gates are full source
coverage and semantic fidelity, two completed real descriptions, actual PDF visual
review, fair base/adapter comparison, final professor-brief audit, and documentation
of measured results. Do not mark the overall goal complete based on mocked tests.

Later in the same work session: prompt version sequential-1.1 adds deterministic
context hints so the request to write an SRS and lifecycle-change facts cannot
become target-system features. Requirement specialists receive only relevant
source evidence and exclusions. Resume now requires matching model/prompt
provenance. The newer base run at data/evaluations/20261027-031319-base passed
introduction, functional, nonfunctional, security, data and networking. Exact
repeated controls are interned as cross-category references; additional authored
acceptance criteria, dimensions, rationale and sources are retained. Architecture
then failed because a literal quote was attached to the wrong source ID. Native
generation now uses paired source-ID/quote alternatives to prevent that mismatch.

Latest check: 42 backend tests pass and Ruff passes; frontend remains 7 passing
tests plus successful build/format/audit from the last frontend change. The live
base retry is currently executing architecture (exec session 94472 when started).
The app server was restarted once and is running via exec session 85147, but
subsequent Python changes require another restart before exercising them through
the browser. No app-root demo projects or real human approvals have been created.
The app-browser tab is http://127.0.0.1:8010 and currently shows the new-project UI.
Check actual handles and persisted run state on continuation; do not infer liveness
from this note. Remaining work still includes complete real outputs, semantic
review, second VPN case, same-final-version base/adapter comparison, PDF visual
inspection, final professor-brief audit, and updating measured documentation.

2026-10-27, later verification: 72 backend tests and seven frontend tests pass;
TypeScript/Vite build, Ruff, Prettier and npm audit pass (zero vulnerabilities).
Added compliance applicability, exact scope preservation, per-source passage
drafting, explicit permission-test checks, and narrowly model-authored completion
of omitted behaviors/tests. Repeated retry failures now preserve inherited partial
passages. Current-rule reads/exports/approval checks cannot trust a stale stored
quality report; original content and hashes remain immutable. Drafting model tags
are preserved across inherited sections and shown in the UI/PDF drafting record.

The copied assets still match all 789 hashes. Direct current-schema validation
finds all 1,038 historical assistant targets incompatible without adaptation;
this does not assess semantic quality and no retraining or label edits occurred.

Real campus output at sequential-1.5 completed with five requirements and Agile,
using adapter-first generation plus disclosed base-Qwen corrections. Manual review
still rejected a narrowed unconditional exclusion and architecture lists that
repeated requirements. Sequential-1.6 therefore requires named components,
resolved flow endpoints, trust-boundary enforcement and all-requirement design
coverage, and rejects newly added conditions on unconditional exclusions. Earlier
complete drafts are not accepted final evidence. Source-faithful current-profile
campus/VPN runs, complete output review, final PDF inspection and the final brief
audit remain required. A real HTTP/UI campus project has been created locally
without invented answers or approvals; it still needs generation under the current
server/profile. See data/ui-evaluation-project.json for its identifier.

Current automated suite: 76 backend tests; seven frontend tests; production build,
Ruff, Prettier, zero-vulnerability npm audit, pip dependency check and local model /
111-chunk knowledge preflight all pass. Source logging scope now applies to SDLC
list fields, unconfirmed workflow roles must be visibly proposed, and an Agile
exit cannot demand that future requirement changes stop. Python setup uses the
tested dependency lock as constraints. No real human approval was recorded.

Earlier-profile VPN also completed (583.7 seconds, V-Model), but manual review
found broadened MFA actors, ambiguous compound permissions and generic testing
phases. These remain defects to address under the current profile. A current
campus run was started through the browser UI in app-root data, with exact original
input and unresolved decisions intact. Generation run:
45b6b0c3-da59-425a-90f7-871dafb9be6e. Inspect its actual persisted state on continuation;
do not infer completion from this entry. Original runtime model digests are in
data/runtime-models-snapshot.json. Earlier development evaluation processes have
terminated; do not restart a live app-root run merely because observation times out.

2026-10-27, profiles 1.14-1.16: 100 backend tests pass (24 third-party deprecation
warnings); Ruff lint and format checks pass for src/tests/scripts. Seven frontend
tests/build/format/audit remain the last passing frontend verification, with no
subsequent frontend changes. The added architecture-edit API regression passes.

Frozen real HTTP evaluations at 13:56:50 and 14:07:11 UTC failed; no accepted
document or human approval resulted. Fixed an overbroad registered-population
check and constrained introduction factual details to their literal source.
Added the deterministic functional index of canonical actor interactions so a
security classification cannot make the functional view falsely inapplicable.
Initial view tests exposed final validation rejecting forward cross-section
references; final assembly now resolves reference IDs against the complete
canonical registry while generation-time checks remain staged. Regression suite
passes after that correction.

A traced production retry reproduced the actual Ollama HTTP-500 native-output
parse rejection, with the runtime still available. Only that exact diagnostic
enters the bounded schema-correction policy; other availability failures do not.
Current frozen HTTP evaluation: data/http-evaluations/20261027-141900, campus
run 3a556bbd-3a02-4db5-8e52-01720d5a1ed3. Read persisted state before starting
another model job. Real semantic acceptance, final PDF inspection, matched
base/adapter evaluation, audit-history implementation and full brief review
remain open. ADR-0017 is a design for pending audit work, not an implementation.

Later checkpoint, sequential-1.21: implemented private append-only audit events,
including exact inference attempts and corrections, source revisions and exported
bytes/hashes. Verified the downloaded real clarification audit. Sparse input
asked three questions; explicit skips remained unknown and were not repeated.
Changed the Ollama wire endpoint to /api/generate after a matched diagnostic,
without changing model weights or semantic validation. See ADR-0022.

Profile 1.19 VPN completed but assistant semantic inspection rejected omitted
25-session capacity, broadened employee MFA and generic V-Model phases. Added
planning-context routing, proposed architecture status/scope checks, precise
verification factors and explicit V-Model planning/test pairs. Profile 1.20 then
exposed permission-validator false positives; 1.21 preserves affirmative success
with a no-error qualifier and recognizes returned log views as inspection.

Checks: 156 backend tests pass (24 third-party warnings); Ruff check/format pass;
7 frontend tests, TypeScript/Vite build and Prettier pass. Refreshed asset audit:
789 files match, historical current-schema targets 0/1,038, no retraining or split
changes. Fresh frozen HTTP evaluation data/http-evaluations/20261027-164444 is
running; no current-profile semantic success or human approval is claimed.

Profile 1.21 terminated with both cases failed, source snapshot unchanged. Campus
failed architecture scope/duration checks. VPN failed after copying old controls
into its exclusion passage and hitting duplicate checks during repair. Accepted
partials also exposed unrequested isolation logs, an unexercised acknowledgement,
and administrator management hidden by a negated operator permission.

Integrated the source/test corrections in profile 1.22 (ADR-0025): action-trigger
coverage, external test-capture versus product logging, affirmative management
role coverage, explicit actor exclusivity, readable bounded correction guidance,
and exact noun-form automation exclusion with both reconfiguration/scanning
tests. One generic fixture assumed an unstated authorization log; it now captures
the actual response/decision. Full main backend: 176 passed, 24 third-party
warnings; Ruff lint/format pass. No frontend behavior changed in this checkpoint.
Asset hashes remain unchanged at the refreshed profile-1.22 audit.

Fresh analysis and frozen HTTP evaluation:
data/http-evaluations/20261027-171155. Campus project
abcefb09-a213-4ba9-a996-8458fa629290, generation
2e8c1912-7623-4242-9c66-c81e7c159785. Read actual outcomes before claiming success.
DATA_HANDLING.md records the existing manual-until-deletion policy and masking
gap explicitly; documentation does not claim an automatic privacy feature.

Profile 1.22 was cancelled after observing a validator false positive: the explicit
witness "test instrumented log" was incorrectly treated as production logging.
The driver was stopped before starting VPN, cooperative cancellation completed,
and the source snapshot was verified unchanged at interruption. Evidence:
data/http-evaluations/20261027-171155/assistant-interruption-review.json.
No semantic acceptance or human approval was recorded.

Profile 1.23 broadens the test-instrumentation wording guard and adds the exact
positive regression. Main backend: 178 passed, 24 third-party warnings; Ruff
lint/format pass; asset audit refreshed with all 789 hashes matching. New frozen
HTTP evaluation: data/http-evaluations/20261027-171656. Campus generation
c1afabe7-7342-4c00-a4ea-5c7074fcf579, project
de2e4906-38a7-4a27-999e-67d4b28b3da9. Actual output review remains pending.

Profile 1.23 campus failed architecture at items_unrequested_logging. Inspection
found the logging regex falsely matched "logical". Its valid partials also contain
a real unsupported isolation waiting period in FR-002. Assistant review (not
human approval) is saved beside the frozen evaluation, with the exact partial
hash. Positive alert review/acknowledgement and attempted policy-change denial
are now actually exercised in the accepted security criteria.

Prepared, but not yet integrated while VPN runs: precise log-word boundaries,
source-supported waiting conditions and fixed corrective guidance. The isolated
development copy passes all 188 tests and Ruff lint. Pending files are listed in
data/audit-development/INTEGRATED.md; main remains profile 1.23 with 178 tests.

Prepared scripts/heldout_compare.py for a matched no-fallback comparison of fixed
historical eval-001/eval-006 descriptions after interactive work is idle. Its
overlap guard correctly refused to start during the live workflow; no comparison
inference has run yet. Dataset provenance check finds no exact normalized full
description matches in 1,038 records across 22 JSONL files. This does not establish
absence of paraphrase/scenario-family overlap or unknown weight contamination.
Dataset SHA and original splits remain unchanged. See data/evaluation-provenance-check.json.

The frozen 1.23 VPN case failed at unconfirmed_actor_exclusivity during management
completion; its exact positive requirement/test was useful but an extra negative
test invented exclusive administrator permissions. The run's assistant review is
saved beside the campus review; no human-approval record was posted.

Integrated profile 1.24 (ADR-0026): source-bound waiting-condition validation,
precise logging-word matching, and explicitly audited rejection of unsupported
extra exclusivity criteria during completion/repair. Preserve remaining authored
tests unchanged; unsupported statements and candidates with no remaining test
still fail. Full source coverage/denial validation runs after normalization.
Main checks: 192 backend tests pass, 24 third-party warnings; final Ruff lint and
format pass; asset audit refreshed with all 789 hashes matching. Development tree
is stale again and must not overwrite main.

Fresh frozen HTTP evaluation: data/http-evaluations/20261027-174444. Campus
project 0870fe65-8a5f-42a6-a960-a089f4aa58dc, generation
67ffc49c-0369-40e1-8162-3e47d9b1073b. Current real correctness is still unaccepted.

Profile 1.24 terminated failed for both cases, source snapshot unchanged. Campus
hit a logging false positive on "logs into" and exposed same-node trust boundaries;
VPN rejected actual dashboard access with visible log data as an unexercised read.
Two rejected unsupported extra tests were recorded in the real VPN private audit.
Assistant review is saved under data/http-evaluations/20261027-174444.

Integrated profile 1.25 (ADR-0027): shared event-log/sign-in semantics, external
logical actor/zone endpoints, distinct trust domains, and role-bound read initiation
with visible data. A button alone remains insufficient. Main checks: 213 backend
tests pass, 24 third-party warnings, final Ruff lint/format pass; asset audit at
1.25 still verifies 789 files. Frontend remains unchanged with its prior 7-test
and build/Prettier passes.

The real retry endpoint started campus run 37d2b88c-a3ba-4c82-b1ca-06a44caff49b
from the failed 1.24 run. Inspection confirmed prompt-version mismatch deliberately
clears old checkpoints, so sections are rebuilt from unchanged saved project input;
this is not evidence of same-profile checkpoint reuse. New frozen evaluation:
data/http-evaluations/20261027-181046. Its VPN case will be freshly analysed.
Actual SRS/SDLC correctness, final PDF review and held-out comparison remain open.

Profile 1.25 failed both cases with unchanged source snapshots: architecture added
unrequested real-time guarantees; required VPN denial copy invented exclusive
administrator powers. Integrated ADR-0028 in profile 1.26: audited source-bound
timing normalization and safe removal of unsupported denial explanations, followed
by full source/test validation. Main: 220 backend tests pass, 24 third-party
warnings, Ruff lint/format pass. Original response and normalization remain private
audit evidence. No approval was recorded.

Fresh evaluation: data/http-evaluations/20261027-232716. Campus project
84b840c5-f0bd-4496-8598-f961e15f2807, generation
964ab132-069a-42bc-8adf-8b8014e2d326. Final output review is pending.

2026-10-28: Profile 1.26 failed campus architecture on an invented minimum
retention bound and VPN SDLC on non-plan TEST references. ADR-0029 extends audited
bare-duration preservation to architecture and stages V-model workflow inventory
before constrained verification links. All four test levels, actual early plans
and post-implementation execution are checked. Separate SDLC generation version
1.2 invalidates only SDLC; predecessor reuse is revalidated and regression-tested.
227 backend tests pass (24 third-party warnings), Ruff passes. Real retry driver
data/http-evaluations/20261028-000439 uses the same saved project inputs and global
prompt 1.26. Do not treat its running status as completion. Assistant review of
previous requirement checkpoints records additional semantic defects in the 1.26
evaluation directory; supported correction and full final review remain required.

The first checkpoint retries reused seven campus sections and thirteen VPN sections.
Campus again failed a self-boundary; VPN reached SDLC linking but exceeded context.
Frozen source hashes remained unchanged. The link context now contains only phase
inventory and requirement statements, and native boundary branches forbid identical
endpoints. ADR-0030 adds source-hash-bound reviewed checkpoint corrections, distinct
human/assistant edit provenance and a saved-section review UI. Tests reject stale
hashes and invalid links and confirm an unapproved immutable result. 229 backend
tests and 8 frontend tests pass; TypeScript/Vite build, Ruff and Prettier pass.
Prepared assistant corrections under data/assistant-corrections/20261028-source-review
remove unsupported exclusivity, mutual authentication and capacity caps, verify
retention deletion by inspecting storage, and provide source-linked logical designs.
All submitted sections pass schemas and current source gates. These are explicit
assistant revisions, not raw model success or human approval. Real dependency
regeneration is running under data/http-evaluations/20261028-001735.

Assistant inspection of the reviewed campus run's newly generated dependent
artifacts found unsupported system-event logging, real-time outcomes, a minimum
30-day scenario and unrelated RAG guidance on automatic isolation. These are
rejected content findings, not accepted semantics. Final derived-section edits
and source-by-source review remain required even if a run completes. No claim
of unassisted model correctness follows from corrected core requirements.

2026-10-28: Revalidated the active Desktop workspace after a no-progress
conversation turn. Integrated ADR-0032 whole-artifact source guards and an
independent quality-policy version. The actual previous base drafts now reject
for omitted firewall/monitoring capabilities, invented phase/test quantities and
claimed recorded approval. Linked criteria use their canonical source when their
own evidence is empty. Retention/deletion tests require actual storage outcomes.
Capability nouns are separate from action-attempt checks, preserving valid
prohibition tests. Focused regressions plus the full suite: 265 passed; Ruff
passed. A first full run exposed that capability/action coupling and was fixed;
the final full run passed. Frontend: 8 passed, build and direct Prettier passed.

Recorded matched comparison, negative model-review experiment, bounded privacy
probe, contradiction probe and assistant-edit disclosures in VALIDATION.md.
Recomputed historical qualities without changing content hashes; report and
current reviewed PDFs are in data/source-grounding-reviews/20261028-042353.
Started a fresh real, trained-first, unedited campus/VPN regression under
data/evaluations/20261028-042259-finetuned. Production source is frozen for this
run; do not infer terminal success from its running process.

The fresh campus run terminated failed after 336.2 seconds with
`targeted_requirement_repair_failed:FR-002:unconfirmed_production_log_witness_use_test_capture`.
Its E-007 batch added an unrelated linked FR-002 criterion with empty evidence and
a production device-management log. Current guards rejected it correctly, but
canonical-row repair does not visit that linked record. ADR-0033 records the
next source-ownership/native-schema and linked-test repair change; implementation
waits for the still-running VPN case so this source snapshot stays reproducible.
The fresh campus draft also had unrequested uninterrupted-access and visible
denial-message wording, so a structurally completed report would still need
semantic rejection. These findings are retained rather than counted as success.

Restarted the idle local app with the tested policy; actual GETs for reviewed
campus/v19 and VPN/v17 report source-grounding-1.1, unchanged hashes and zero
human reviews. UI access verified campus/v19 and its evidence-based Agile score.
Screenshots are beside the current re-exported PDFs. No generation was started
from the UI and no approval recorded.

The frozen trained-first evaluation has terminated: campus failed after 336.2s
on unrelated linked production-log evidence; VPN failed after 1231.9s at
verification on an unsupported numerical commitment. Its terminal stability file
confirms production source stayed unchanged throughout both cases. No completed
new SRS or human approval was created. Inspecting VPN checkpoints additionally
found concurrent inventory misuse, invented session caps, mutual authentication,
unnamed privacy-regulation claims and unsupported risk labels. Passing individual
old gates did not establish correct meaning.

Implemented ADR-0033 in an isolated source copy while the frozen run finished:
source-owned native linked-test targets plus independent parser checks, bounded
linked-criterion replacement preserving valid siblings/target IDs, additive named
capability completion, observable-denial prompting, and guards for the newly
observed claim classes. Profile 1.27 / source-grounding-1.2. Full staged suite:
285 passed, 24 third-party warnings; Ruff passed. Promoted only seven reviewed
modules after confirming the old run was terminal and every original module still
matched its frozen hash. Before-promotion copies are retained in
data/grounding-development/20261028-linked-source/before-promotion.

The stricter risk-label policy also rejects inferred impact labels in campus/v19
and VPN/v17. Those assistant-reviewed examples are not exempted or silently
rewritten to keep demonstrations green. Their previous policy results and exact
exports remain historical evidence. Current raw-generation correctness remains
unproven; new evaluation under the integrated profile is required.

Integrated main verification: 285 tests passed, 24 third-party warnings; Ruff
passed. The workspace-local fresh test base avoided the default Windows cleanup
warning. Restarted the idle app with integrated sources and started a new real
profile-1.27 campus/VPN run in data/evaluations/20261028-045259-finetuned. It uses
adapter-first policy, captures actual model tags/source hashes, and supplies no
assistant edits, fabricated answers or approvals. Do not restart a live handle
because an observation expires. Current original/reviewed content remains
immutable and the overall goal stays incomplete pending actual output review.

UI inspection exposed that current invalid quality still used the normal draft
badge. Updated it to an explicit red "Invalid draft · validation failed" state.
Added a rendered regression covering historical approval plus current invalidity,
without submitting a review. Frontend: 9 passed, TypeScript/Vite build and
Prettier passed. Actual browser screenshot ui-invalid-policy-1.2.png and live
API confirm invalid current campus/v19, unchanged hash and zero reviews. This
frontend-only change does not alter the frozen Python evaluation source profile.

2026-10-28: The frozen profile-1.27 run terminated with source stability true.
Campus completed in 945.8 seconds with five requirements and the expected Agile
label, but assistant review rejected nine content defects: invented category
prose, missing network domains, unsupported scenario conditions/logging, unrelated
RAG citations and a linear Agile workflow with unconfirmed delivery roles. VPN
failed in 796.9 seconds on DR-001's unsupported privacy-regulation rationale.
Actual artifacts/findings remain in data/evaluations/20261028-045259-finetuned;
no complete automatic SRS was accepted and no human approval was recorded.

Promoted ADR-0034/0035 metadata and lifecycle changes after the frozen run ended.
Main verification then passed 295 backend tests and Ruff. The first real focused
probe, data/category-lifecycle-probes/20261028-053155, failed with unchanged input
and source: empty category links and a final linear SDLC. A middle SDLC correction
had real iteration but coverage/quantity/approval errors; later feedback forgot
the iteration diagnosis. This observed regression motivates ADR-0037 rather than
claiming the workflow is correct because its methodology name matches.

Integrated metadata 1.1 canonical-topic links, shared parser validation, ADR-0036
field-only rationale correction with the actual rejected requirement, and
bounded-corrective-history-1.0. Diagnostic rationale substitutions never persist;
all actual correction text still comes from the local model. Private typed
candidates remain untrusted, masked again on retries and omitted whole if only
that auxiliary context exceeds capacity. Authoritative inputs are not truncated.
Staged focused checks: 11 passed. Main full suite: 301 passed, 24 third-party
warnings; Ruff passed. Backups of the four promoted modules are under
data/field-repair-development/20261028-source-repair/before-promotion-20261028-0646.
The idle server was restarted with tested source. Stopping its verified child
also ended the parent; the parent identity guard then reported it absent. The
new server runs independently; no active workflow was stopped.

Second real focused probe: data/category-lifecycle-probes/20261028-060409. It uses
the production category gate and the same compact verification keys as runtime.
The trained adapter returned all three known network controls on its first
category attempt (8 seconds). That narrow result has an assistant review; SDLC
remains running. These are section probes, not full SRS correctness, unseen data
or human approval. Frontend was unchanged (previous 9 tests/build/Prettier pass).

2026-10-28 follow-up: The second category/lifecycle probe terminated with source
and input stability true. Category links were correct for the inspected scope;
SDLC failed in 368.6s. Actual wire requests retained all accumulated diagnostics
and the prior candidate, but the model only relabelled a test-only phase as
iteration. No complete SDLC success follows from the working retry mechanism.

Real rationale probe 20261028-061325 changed only DR-001's rationale (15.1s);
assistant review rejected the unchanged deletion-event log and incoherent WHEN.
ADR-0038 fixed the source-log-noun bypass; initial regressions failed as expected,
then 308 staged and 309 integrated tests passed, with Ruff clean. The actual
20261028-061533 repair then failed on the regulation claim during whole-row
correction (52.7s). Both probes retained unchanged source; neither is a correct
SRS. Criterion-first repair is staged under field-repair-development/20261028-criterion-first.

Implemented ADR-0039 typed Agile cycle composition, keeping public phases and the
V-Model path unchanged. Integrated 318 tests passed, 24 third-party deprecation
warnings; Ruff passed. One new test initially supplied unassigned requirement IDs;
fixed the fixture to use normal ID assignment and reran successfully. New real
probe: category-lifecycle-probes/20261028-062008. Production source is frozen
while it runs. No weights, datasets, stakeholder answers or approvals changed.

The typed-cycle 1.5 probe terminated failed after 341.4s with unchanged source
and input. Its actual drafts had build/test/feedback/backlog work, but a per-action
pattern rejected additional refinement actions that did not repeat backlog. SDLC
1.6 removes that unnecessary per-string restriction while retaining full-cycle
return validation. The added regression accepts refinements alongside a return
and rejects the missing-return case. Criterion-first repair is also integrated;
staged full suite 319 passed, integrated full suite 320 passed (24 third-party
warnings), Ruff passed. One targeted test invocation named a nonexistent file
and ran no tests; the corrected focused tests and complete suite then passed.

The user explicitly requested a test using the normal local model without the
adapter and a chat verdict before changing the default. Started a fresh full
base-only campus/VPN run in data/evaluations/20261028-072314-base using
qwen3:4b-instruct-2507-q4_K_M, with no adapter provider/fallback. Production source
is frozen for the run. Actual model tags/digests/requests and outcomes are retained.
The default remains adapter-first; no misleading adapter attribution is introduced.
A source-by-source review plan was saved beside the evaluation. Do not confuse
generation completion or a matching SDLC label with correct content.

Requested base-only verdict: data/evaluations/20261028-072314-base terminated
with both workflows failed (campus 180.7s, VPN 101.4s). Read the actual rejected
text: campus lacks an explicit acknowledgement action in its acceptance WHEN and
initially adds unrequested event logs/messages; VPN preserves an invented "up to
250 users" cap in its introduction despite original registered-user planning
inventory. Audit: 20 requests, only the normal Qwen tag, zero adapter calls, zero
complete versions, zero human reviews. Source stability true and independently
rechecked against the manifest. Saved assistant-verdict.json. No completed SDLC
or PDF can be claimed. Default model remains unchanged, as requested pending the
chat verdict. Software checks remain 320 passed/Ruff passed; real output checks
failed. No source edits were made during evaluation.

2026-10-28 continuation: Adapter configuration/readiness was revalidated; no
model default change was needed. Previous base-only evaluation supplied negative
evidence (progress); the readiness-only confirmation did not establish SRS quality.
Implemented ADR-0040 source-bound supplemental permission actions, compact model
context and acknowledgement-specific correction. Focused 18 tests passed; full
322 passed/Ruff passed after formatting fixes. Restarted the verified idle server
(handle 39369) and ran frozen adapter-first campus/VPN evaluation
data/evaluations/20261028-075702-finetuned (handle 81716, now terminal). Both failed:
campus 318.2s at compound automatic-exclusion test completion; VPN 183.3s on an
introductory invented capacity cap. Stability true, source hashes independently
matched before later promotion. The campus WHEN merely said "the action is
executed" while GIVEN named isolation; it did not exercise both forbidden actions.
VPN additionally reopened continuous delivery despite the explicit exclusion.
No completed SRS/SDLC, dataset edit or human approval was created.

Implemented ADR-0041 canonical criterion verification views in an isolated copy,
then promoted seven allowlisted modules after the frozen evaluation ended. The
local model classifies all canonical/linked criteria; exact authored GWT/evidence
text composes the public tests. Duplicate/missing/unknown/method-changing choices
are rejected. New provenance supports selective retry and honest explicit edits;
current quality checks the claimed projection against actual canonical content.
An initial retry regression unnecessarily redrafted glossary; fixed selective
reuse and verified repeated retries retain projection provenance. Staged and
integrated full suites passed 334 tests; Ruff passed. Backups remain under
data/verification-development/20261028-canonical-projection/before-promotion.

Actual verification probe 20261028-081559: adapter first attempt, 11.1s, eight
criteria retained exactly; inspection rejected the boundary label on an automation
exclusion and noted upstream audit-field/retention-procedure limitations. Projection
1.1 constrains outcomes/quantified boundary eligibility. A noun-success ambiguity
(connectivity/session establishment) was exposed in regressions and actual labels;
fixed verb recognition and used the explicit canonical automation prohibition for
negative classification. Final software checks at that step: 337 passed/Ruff pass.
Probe 20261028-082545 retained eight criteria in 5.0s on first adapter attempt,
but its pre-fix denial label still needed correction. Neither is a complete SRS.

ADR-0042 per-action exclusion completion is now integrated: source-grounding-1.7,
field-local-repair-1.3. Keep the aggregate final gate, complete actual missing
actions separately, allow one valid combined test to close several gaps, keep
actions explicit in WHEN, respect active scan mode and use relevant traffic/state
evidence. Staged full tests initially rejected a valid network-trace synonym;
fixed recognition without accepting configuration-only scan evidence. Staged and
integrated full suites: 342 passed (24 third-party warnings), Ruff passed. Four
module backups are under acceptance-development/20261028-action-at-a-time/before-promotion.
Source-scoped real completion probe 20261028-084057 (handle 21827) uses actual
rejected rows, exact evidence and unchanged assessment labels; only the assessment
set is scoped to the rejected source. It is not a full-document correctness claim.

The source-scoped real exclusion probe 20261028-084057 is terminal and completed:
two trained-adapter calls, 11.2s, no base correction. Source stability true; actual
inspection confirms explicit automatic isolation and firewall modification in
WHEN, no applied changes and before/after evidence. Normative fields remained
unchanged; only rejected criteria were replaced. It is not a full SRS proof.
The final verification probe 20261028-084438 completed on one adapter attempt in
4.9s, preserving all eight criteria with appropriate positive/negative/inspection
labels after the noun-success fix. Source/input stability true; upstream audit-
field/retention-procedure limitations remain. Saved bounded assistant reviews.

Implemented ADR-0043 source-fact introduction: trained specialist organizes every
source ID once; canonical narrative retains exact statements, source status,
questions and unresolved decisions. The fixed overview describes the document,
not invented product commitments. Moved scope preservation to source_facts.py and
retained the public validation re-export. Exact short answers are not padded;
the eight-character narrative check remains everywhere except an exact intro
quotation. Copied question context is source metadata, not a new quantity.
Selective retry and reviewed-edit provenance mirror verification projection.
Focused 11, baseline 55, staged full 353 and integrated full 353 tests passed;
24 third-party warnings; Ruff passed. Eight promoted modules have backups under
data/introduction-development/20261028-source-facts/before-promotion.

Restarted the verified idle backend after tests (handle 9552). New full adapter-
first campus/VPN run: data/evaluations/20261028-090128-finetuned, handle 96695.
Source is frozen for the driver; no assistant section edits, stakeholder answers,
dataset changes or human approval. Inspect the actual terminal result and full
content before any success claim; the overall goal remains active and incomplete.

The fresh 090128 full run terminated failed in both cases before intro inference:
a native schema preparation KeyError assumed every introduction schema had Claim
definitions. Preserved the failed run/stability. Fixed the schema-kind guard and
made the native-order regression use the actual assigned_section context; focused
20 and full 353 tests passed, Ruff passed after import formatting. Restarted the
verified idle server (handle 92201). A read-only SQLite backup created a separate
retry evaluation, 20261028-090700-finetuned-native-fix, preserving original failed
artifacts and model-authored analyses. Resume origin/source input hashes recorded.
The actual retry driver handle 45103 is now terminal. Both introductions completed
with exact source facts; campus then failed at a witness's invented uninterrupted
availability promise (99.4s), VPN at a missing-administrator completion that copied
an error-message/audit-log witness (803.1s). Source stability true. No full SRS,
SDLC or PDF success follows.

ADR-0044 is staged under data/acceptance-development/20261028-witness-local:
observable-evidence-only schema and merge when that is the sole criterion defect;
full criterion repair otherwise; known creation-only deletion-trigger check for
canonical and linked tests; compact completion context; typed completion recovery
through the same criterion gate. Private GenerationError metadata records actual
rejected author/total failed attempts, including primary/base handoff, so recovered
rows cannot be misattributed or undercount calls. No recursive full-section retry.
Existing linked-witness regression was updated to prove a typed field patch cannot
change its target ID; data tests still require full-criterion repair for the known
incoherent temporal step. Focused 17 tests pass; initial field-only full 358 passed.
The completion/provenance follow-up full suite passed 361 tests (24 third-party
warnings); Ruff passed. Handle 39836 is terminal. Current main remains 353-tested source-grounding-1.8.
The probe CLI now supports source-scoped functional repair, reuses valid partial
siblings and retains original assessment labels/evidence; those are evaluation
scoping choices, not assistant edits or a complete-SRS claim.

Promoted ADR-0044 modules; main full 361 passed, then added exact failed-initial-
passage attempt accounting with a parametrized production-path regression. Main
full 362 passed/Ruff passed. Live readiness confirms adapter as primary and ready
(cybersrs-qwen3-4b-ft:latest); base correction remains enabled. Reported enabled
to the user. Actual probes 101155/101211 terminal; saved assistant reviews: campus
witness-only repair bounded success, VPN additional row rejected for invented
creation/revocation/group/database/audit details. No source edits or human review.

ADR-0045 implements recognized permission-management source scope, exact bounded
completion statement/native and independent gate, plus missing audit/access-control
log-class checks where only existing connection logs are stated. Initial full run
failed three fixture statement expectations; aligned fixtures with the new source
contract and retained independent rejection checks. Final integrated full 365
passed (24 third-party warnings), Ruff passed. Historical counts above record
their own runs. Current-source VPN real probe is running; keep source frozen.

Probe 101910 is terminal, selected fixes verified with source stability true and
a saved bounded assistant review. Restarted verified-idle backend with integrated
1.10/1.5 (handle 14497), adapter primary ready. Read-only SQLite backup created
separate evaluation 20261028-102047-finetuned-management-fix with origin and exact
input hashes; unchanged analyses and valid checkpoint siblings are reused, no
assistant sections/answers or approvals. Full driver is now running; source frozen.

ADR-0046 is staged under architecture-development/20261028-source-endpoints.
Recognized source access pairs produce frozen logical actor/resource nodes; the
model still authors implementation blocks and directed interactions. Independent
gates require named source endpoints and requirement-linked directed paths, so
internal-module prose cannot substitute for actual internet/staff-network targets.
Architecture context omits acceptance-test assumptions and keeps canonical source
statements. Equivalent manual endpoint names remain allowed. Staged focused 29
and full 373 tests passed (24 third-party warnings); Ruff passed. New tests and
all changed backend modules stay in the isolated stage. Main remains integrated
365-tested source-grounding-1.10; the live driver 34062 remains running and main
source unchanged. Campus has reached architecture after requirements/security/
data/network/compliance. No full content/PDF/SDLC success is asserted.

Main campus run terminal failed after 800.2s on architecture policy-change audit
scope. The staged gate independently finds missing source actor/internet/staff
network nodes in the actual rejected draft; saved bounded topology review. Staged
architecture overview now has a native fixed metadata constraint and independent
check, avoiding summary-level invented global audit promises. Focused 26 tests
and Ruff passed after that change; the prior staged full 373 pass precedes this
small overview follow-up. Prepared isolated actual architecture probe driver
which requires terminal source evaluations and no active interactive runs. Main
full handle 34062 remains running on VPN; do not promote/restart while it runs.

Full driver 34062 is terminal exit1. VPN failed after686.7s on truncated
capacity-completion output (sourceE006:250 registered users/25 simultaneous
sessions), not administrator management. Independent full source hashes match
and stability is true. Actual response inspection shows complete typed prefixes
with an invented maximum25 limit followed by repeated closing garbage; raw
truncations remain rejected, not accepted as canonical data. No full SRS versions.

First actual staged architecture probe141045 (handle57833) is terminal failed
after109.9s on missingFR003 ownership; source stability true. It retained the
three real source endpoints and the scope-neutral overview. Added a bounded
owner-link stage for missing canonical obligations: model selects an existing
implementation component, server appends the exact canonical source statement
and links without a new automation engine or changed endpoint cards. Native
ID/name vocabulary and independent exact coverage/owner checks apply. Full
staged tests are running; main source remains unchanged.

Actual architecture142342 passed selected gates but assistant review rejected
wrong-role student/admin/operator flows and false regulatory/audit authority.
Preserved its negative review and before-layout-plan source snapshot. Replaced
the isolated internal protocol with source-backed layout DTOs: model chooses
component grouping, exact owner links, directed pairs and trust-domain pairs;
server composes canonical duties/actions/enforcement/citations without free new
product claims. Added all recognized source actor cards and role-specific row
bindings. Role paths must reach the proper implementation owner; access paths
must reach the real resources. Public architecture schema stays compatible.
Initial staged full failed14 tests using old bulk-schema fakes; updated those
fakes to the new internal DTO boundary and retained full API/revision checks.
Final staged full378 passed (24 third-party warnings), Ruff passed. Additional
8 qualifier tests passed after explicitly testing rejection of a free enforcement
field. Actual layout probe145243 is now running (handle43857); stage source frozen.

Terminal-padding experiment ADR0047 full386 passed only on software fixtures.
Actual-wire classification finds zero eligible closing-only suffixes out of11
length responses: seven include other content after a complete prefix, four have
no complete prefix. Strict helper correctly refuses these; no replay success or
actual fix is claimed, and no parser cleanup is promoted. The VPN single-row
completion inherits full-section instructions/fields and an irrelevant management
instruction, so fresh subtask context is the next justified correction.

The mediated-layout-only model probe150152 failed after46.2s; it again omitted
required access paths. Final source-backed-layout1.1 compiles necessary source
paths from actual model-chosen owners. A shared owner is selected by a typed
model call, and optional internal relationships remain model proposals over
shared/dependent canonical duties. Actual probe153006 completed in7.9s on two
adapter calls, no base correction; source stability and independent hashes true.
Bounded content review confirms proper actors, owner-mediated targets, explicit
denied attempts and unchanged canonical duties/citations. Upstream FR001/FR002
source issues remain; this is not a complete SRS/SDLC proof. Nine allowlisted
modules and five test files were promoted with before-promotion backups. Final
integrated full380 passed (24 third-party warnings), Ruff passed. No parser
cleanup from ADR0047 was promoted. Main backend reload and complete-campus retry
are next; overall goal remains active and incomplete.

Reloaded the verified-idle backend with integrated1.12/layout1.1 (handle85798).
New one-case full-campus driver73244 is running in20261028-155440-finetuned-layout
from a read-only backup of the failed prior evaluation. It reuses unchanged
model-authored analyses and revalidated earlier sections, with no seeded edits or
approvals. Main source is frozen while this handle is live.

Stage ADR0048 full372 tests passed, Ruff passed. Its prepared completion probe
refused input because E006 has no accepted batch: the exact source checkpoint is
a rejected two-row250/25 cap draft, not an accepted row. No actual model call
was made by that failed probe. Inspection also finds the metric coverage checker
does not equate concurrent and simultaneous, falsely requesting an extra25 row.
Next fix alias handling and repair invalid normative scope before criterion-only
repairs; run the real rejected-section path instead of fabricating a source row.


## 2026-10-28: Completed campus draft rejected after content review

The actual finetuned layout run `20261028-155440-finetuned-layout` completed in
457 seconds. Source hashes independently match its manifest. Version
`6ab3b0b8-c56e-48e3-9e60-1f845a9e56ad`, hash
`eafc4d5b0037a86d7e89f9649ce722f8f5c250d596fb6dacd8ac963646c4324d`,
passes selected automated gates but is rejected for semantic fidelity. The
exact-hash assistant review is saved beside its JSON/PDF. It identifies assumed
authentication/UI details, permitted activity mislabelled as threats, an automated
isolation mitigation contrary to the unconditional exclusion, a reversed scenario
goal, and SDLC cadence/control/technology inventions. Agile ranking alone is valid
evidence for the ranking, not the workflow's correctness. No human approval.

Rendered PDF pages 1,7,10,18,25,30,31 inspected: sampled typography, provenance and
traceability are legible, with no observed clipping. This is a sampled layout
inspection, not an endorsement of content or a full 31-page visual audit.

An isolated source-scope repair stage passed 379 tests and Ruff. Its first actual
VPN E-006 probe `source-repair-probes/20261028-163452` failed in 44.375 seconds: the
model still repeated the invented inventory upper bound in the rationale. Source
stability true; negative review saved. Further stage changes remove rejected
claims from invalid-scope prompts and bind recognized quantity statements to
original source facts. Main runtime remains the previously tested adapter-first
version until isolated checks and real output justify promotion.


## 2026-10-28: Teacher-demo output fidelity changes

Current scope prioritizes a usable teacher demonstration within the user's two-hour
window; full research/benchmark completion is not claimed. Source-grounding1.14
and field-local-repair1.6 are integrated. The exact rejected VPN250/25 capacity
probe20261028-165201 completed in152.172s/8calls. Bounded review accepts corrected
inventory/load scope, preserves model-authored inspection/execution criteria, and
leaves above-load behavior unconfirmed. This is not a full-VPN success claim.

Scenarios now retain canonical source statements and complete authored flow text;
local models choose source actors/alternates. SDLC2.0 compiles source-linked tasks,
actual tests and method-specific cycles/V pairs from model explanations/work
groups. Threat/risk/glossary specialists select source-derived advisory candidates
without new product controls or measured ratings. Native single-role permission
constants prevent broader statements, while unprovided authentication-flow and
infrastructure claims receive corrective diagnostics. ADR0049-0052 document the
changes and their limits. These finite source recognizers are not universal
semantic entailment or threat completeness proofs.

Integrated426backend tests passed; focused15new advisory/scope tests passed after
removing a fixture serializer warning. Ruff src/tests/scripts passes. Frontend9
tests and production build pass. Actual HTTP demo run7253 started with frozen
production sources in data/demo-evaluations/20261028-172238. It creates real
UI-visible teacher-demo projects from unchanged campus/VPN inputs; no fabricated
answers, seeded section replacements or human decisions. Backend11514 is loaded
with this source profile; adapter is primary and knowledge111chunks ready.

Browser inspection confirms the current campus project, sequential progress and
original brief are visible. UI progress screenshot is saved with that evaluation.
Terminal outcomes, full content and PDF reviews are still pending.


## 2026-10-29: Teacher-demo artifacts and resumed VPN repair

The campus HTTP run b542a593 completed in432s with five canonical requirements,
Agile, matching source constraints,26/26selected gates and no recorded reviews.
Version cff620dc/hash d9754783bc42f0a3f4125ddb70d0ae7126c4c388817b0d0dc28565d948a41596
was reviewed as a usable prototype draft, not a fully approved SRS. Its exact-hash
review identifies remaining login/interface/audit fixture assumptions. Sampled
PDF pages1,5,14,17,23,30 are readable; architecture paths and SDLC/task links were
inspected. Production PDF lists now render individually; the same content exports
as31pages in demo/Campus SRS and SDLC.pdf, alongside JSON/Markdown and a guide.
No canonical section was hand-replaced or human-approved.

The previous runtime stopped; the old VPN run became process_restarted/interrupted.
Resumed VPN113ecbef then failed on invented database and24-hour log inspection
behavior. Fresh criterion repair now omits those rejected examples, and source-only
role-denial repair preserves the actual support-operator boundary without inventing
exclusive administrator authority.428backend tests pass; Ruff passes.

Automatic command review blocked a combined stop/restart of the old server
('blocked by policy', without a detailed reason). Instead of terminating that
process, the updated deployment starts on free loopback port8011. .env/README/demo
guide reflect it. Current final app is Qwen-ready with111chunks; the verified
campus document and PDF link were inspected in the browser.

VPN retry53427560 is now live on that build. Source files remain frozen until
its terminal result. The earlier source profile stayed unchanged until its
terminal failed result. Full two-case automatic correctness is not claimed yet.


Teacher-demo delivery audit: final local app8011 is ready, requested adapter tag
confirmed, JSON/hash matches stored Campus version, PDF/Markdown/JSON file hashes
verified,31-page list layout sampled, five requirement trace rows retained,
Agile confirmed, no real reviews/approvals recorded. Demo/ contains the report,
quick guide, presentation notes and UI screenshot. Full latest suite428passed;
frontend9passed/build pass. The latest VPN run failed source validation and is
explicitly excluded from demo-success claims. The rough prototype demonstration
is usable; full research/source-correctness completion remains open in Roadmap.


## 2026-10-29 - bounded generation and section timers

The performance goal is verified on two fresh full generations, without section
checkpoint reuse: university VPN run b58f9cdf-a2ef-4b66-9f99-56b534c3f5cf completed
all 14 sections in 96.768 seconds (slowest 22.027 seconds), and campus-access run
0eae7064-0601-48e0-ac95-8ef659710c2f in 84.166 seconds (slowest 27.482 seconds).
These times exclude prior analysis and PDF export; exports took 0.797/1.000 s.
Both original descriptions match stored canonical JSON exactly. Draft PDFs have
26/31 pages and were sampled visually. Actual primary/corrective model tags are
preserved; no real human reviews or approvals were recorded.

Installed changes: source-ID keyed requirement batches, task-local corrections
that preserve valid fields and confirmed source quantities, source permission
and prohibition test contracts, exclusive residency of the configured main-model
variants, private streaming stopped at complete JSON, an absolute socket-read
budget and bounded lock/retrieval waits, and persisted live/finished UI timers.
The configured section budget is 60 seconds; timeout/failure is never a completed
SRS. Completed analysis is explicitly distinct from completed generation.

Verification: 439 backend tests pass (24 existing third-party warnings), Ruff
passes, all 12 frontend tests pass, and the TypeScript/Vite build passes. New
checks cover continuous output, a silent stalled socket, held inference/retrieval
locks, source-preserving corrections, timer ticking/freezing/reuse, and analysis
vs SRS completion. Earlier campus failures are retained in the evaluation folders;
the final two runs above both complete on the installed profile.

Evidence: demo/final-performance-20261029/Generation timing report.md and each
case's run.json, timing.json, srs.json and SRS.pdf. This verifies the performance
feature, not all research/Roadmap gates. Both documents remain needs_review;
compound requirements may still need additional clause-level acceptance tests.


## 2026-10-29 - NAC access-purpose validation fix

Fixed a false rejection of the NAC purpose phrase "manages access": equivalent
model wording such as "provide secure network access" now satisfies that purpose.
The exception is limited to system-purpose access-service clauses; administrator
management of policies, accounts and permissions still requires its own behavior.
Absent, negated and unrelated audit-log access remain rejected.

The actual saved corrective response from run
31fc79fc-ae99-4c54-b2b0-8bcc9f8ff9dd now passes the production compact functional
composition and validation path (four requirements). Evidence is recorded in
data/performance-development/nac-saved-output-validation.json. Per user request,
no model calls or fresh generation/retry were performed, and no SRS version or
human approval was created. A complete new live NAC run remains unverified.

Verification: 451 backend tests passed (24 existing dependency warnings); Ruff
passed. Twelve new regression cases cover equivalent wording and negative cases.
Frontend unchanged; no frontend tests repeated for this backend-only fix.


## 2026-10-29 - embedded NAC administrator architecture paths

Run 242c151d-ca0b-4917-94f6-33301573a4fd stopped at architecture with
missing_data_flows and missing_trust_boundaries. Its model chose four disjoint
implementation owners. The source actor extractor recognized sentence-initial
roles but missed embedded "allow network administrators to define" and "allow
administrators to revoke" clauses, so no necessary source request paths were
compiled and no internal shared/dependent pairs were eligible.

Recognize affirmative embedded allow-role-to clauses and retain the exact role
and its canonical requirement IDs. Reject conditional/negated clauses and clause
fragments mistaken for roles. Existing architecture gates remain enforced; no
arbitrary internal coupling, new permissions or source edits were added.

Offline replay of that run's actual component selection through the production
architecture generation/validation path passes, with two administrator request
flows and two trust boundaries. Evidence is in
data/performance-development/nac-saved-architecture-validation.json. No model
inference or live generation/retry was performed, respecting the user's earlier
instruction; later sections and full fresh NAC completion remain unverified.
No live SRS version or approval was manufactured.

Verification: 463 backend tests passed (24 existing dependency warnings), including
12 new embedded-role regression cases. Ruff passed. Frontend unchanged.


## 2026-10-29 - SOC monitoring-purpose wording

SOC run eb2b3ff6-6c24-443c-a85c-4966e76ed1dd stopped with
E-001:missing_functional_behavior_monitoring. Both actual adapter and base
responses retained the source's collection of security events from all specified
sources. The capability checker incorrectly required a separate literal monitor
verb from the monitoring platform's name.

Accept affirmative security-event collection/ingestion/reception for a monitoring
product-purpose clause whose source body explicitly states event collection.
Explicit monitoring duties in the body remain required. Negated collection,
unrelated event collection and unrelated product behavior do not satisfy it.
No requirement, test or live input is rewritten by this exception.

Both saved real functional responses now pass production compact composition and
validation without a new model call. Evidence is stored in
data/performance-development/soc-saved-output-validation.json. No generation or
retry was started, respecting the user's earlier no-rerun instruction. No live
SRS version or approval was created. Complete fresh SOC generation remains
unverified and is not implied by the saved-response checks.

Verification: 477 backend tests passed (24 existing dependency warnings),
including 14 new monitoring-purpose cases; Ruff passed. Frontend unchanged.


## 2026-10-29 - research-laboratory live generation repair

The exact new laboratory brief was analysed and exercised through the running
local API. Initial fresh run 7a6fe1b2 failed on unrequested deadlines/logging;
08a89d30 and 2904b308 narrowed remaining model-authored repair defects.
Compact correction now admits the numeric-specificity diagnostic, freezes a
valid outcome for witness-only defects, exposes the original WHEN as repair
focus, and constrains rejected product-log witnesses to model-selected external
test-capture labels. Full semantic/schema gates remain in place; no canonical
section or run status was manually replaced.

Final fresh run f9dc16b1-ec0f-438b-b8eb-19163722d1d5 completed all 14 sections
in 104.151 seconds, with zero reused sections and no manual retry inside that
run. Functional requirements were slowest at 42.078 seconds. The original brief,
canonical hash and final source-profile stability were verified. Exported PDF is
24 pages, with pages 1, 5 and 24 sampled visually. The browser shows completion
and all section timings. Primary adapter and actual base corrections are recorded;
no human approvals/reviews were recorded.

Final checks: 479 backend tests passed (24 existing dependency warnings); Ruff
passed. Frontend unchanged. Evidence, retained failures, PDF/JSON/Markdown, UI
screenshot and explicit remaining content issues are in
demo/research-labs-20261029/Generation result.md. The draft's device-certificate,
audit-field and off-hours-denial assumptions plus alert/isolation acceptance gaps
still require review; execution success does not establish semantic approval or
general one-run reliability on every new brief.


## 2026-10-29 - DNS/web-filtering source-role check

The exact Example 2 brief uncovered two runtime bugs: run 906f9bb1 stopped at
scenarios:source_actor_requires_clarification because "Administrators should be
able to create" was not parsed; c0704c0f then stopped on case-only duplicate
architecture nodes. Extended the shared role parser for affirmative modal
abilities and explicit dashboard recipients, preserving literal canonical bindings
and negative/conditional guards. Source endpoint nodes and compiled paths now
share case-insensitive identity without merging different role qualifiers.

Final fresh run defa0366-2d5a-4cf7-a5b0-9351fe2812c0 completed all 14 sections
in 107.266 seconds with zero reused sections; the slowest section was 27.953 s.
The unchanged brief, canonical hash, model authorship, source-profile stability,
26-page PDF, requirement IDs and completed browser state were verified. PDF pages
1, 5 and 26 were sampled visually. No human approvals or manual section edits.

Tests: 495 backend tests passed (24 existing dependency warnings); Ruff passed.
Sixteen new cases cover source-role modals, dashboard recipients, negative and
conditional forms, literal scenario actors, case identity and distinct qualifiers.
Frontend unchanged. Evidence and retained failures are in
demo/dns-filtering-20261029/Generation result.md and result.json. The draft still
contains automated-investigation, dynamic-scaling/failover and log-field assumptions
and missing policy-update/restriction acceptance tests. Generation success does
not establish semantic approval or full project completion.


## 2026-10-29 - concise IEEE 830-1998 reader and exports

Completed the requested presentation change in the independent Desktop checkout.
A derived typed reader follows the IEEE 830-1998 numbered outline, uses simple
source-aware User/Admin/Project Analyst labels, preserves introduction wording,
and prints every canonical requirement once. The app reader and default PDF/MD
share this presentation. Full criteria, architecture, SDLC, provenance and editing
remain available through supporting details and full exports. Immutable content,
source citations, draft status and hash-bound approval remain intact.

Live current-API exports of the unchanged DNS and laboratory saved versions are
five pages each (previously 26 and 24). Five of five canonical requirements and
exact introduction/content hashes were verified in each. All ten primary PDF
pages were visually inspected; actual browser screenshots show the reader and
stakeholder table. No generation, model change or human decision was performed.

Final checks: 502 backend tests passed (24 existing dependency warnings), 16
frontend tests passed, Ruff passed and production build passed. The live-format
verification script also passed both cases, including full supporting exports
and runtime readiness. Evidence, reproducible checks and the requirement-by-
requirement completion audit are in
`demo/ieee-830-20261029/Formatting verification.md` and `verification.json`.
This completes the formatting scope only; existing semantic issues and SDLC
selection limitations remain separately documented. No full-product completion
or human approval is inferred from presentation checks.


## 2026-10-29 - four supplied live examples and bounded source repairs

Ran the exact supplied campus Wi-Fi, email gateway, endpoint monitoring and
firewall briefs through the running local API. The initial pass completed Wi-Fi
and email; endpoint and firewall failed. Preserved every attempt. Fixed the
managed-endpoint adjective and system-event monitoring-purpose false positives,
strengthened source-ID binding, and added schema-bounded model-authored repair
only for recognized invalid source groups. A later firewall run completed but
recast the project Design request as a runtime feature; another fresh run's
repair returned a non-normative raw request. Added the request-verb guard and
normative repair schema. No gates were disabled, no output/success was manually
inserted, and the 60-second section budget stayed unchanged. See ADR-0055.

Latest selected fresh completions: Wi-Fi 89.649 s, email 55.067 s, endpoint
41.495 s, firewall 81.364 s. Each completed 14 sections with zero reused sections,
zero section edits and no manual Retry within that run. Wi-Fi/email/endpoint ran
sequential-1.29; firewall ran sequential-1.30 after the final normative-schema fix.
Current API validation, original brief, exact canonical hash, all PDF statements,
export byte identity and zero human decisions were verified for all four. Source
hashes were stable during each selected run; the deployed release profile was
also checked against current source bytes. All twenty primary PDF pages were
inspected visually. PDFs use the default IEEE outline and are five pages each.

Saved all four PDFs plus a timing report on Desktop/CyberSRS - Four Examples.
Full supporting reports, exact inputs, preliminary failures, source snapshots,
runs, canonical versions and verification evidence remain under
`demo/four-examples-20261029`. The reproducible assemble_results.py check passed;
a targeted authored-prose scan found no excluded concrete implementation/limit
choices. Unresolved questions and library quotations are separately identified,
including an unanswered Wi-Fi protocol example, rather than treated as decisions.

Checks: 516 backend tests passed, 24 existing dependency warnings (37.90 s);
41 focused correction/wording tests passed; Ruff passed for src/tests/scripts and
the development drivers. Frontend unchanged and not rerun in this task. Added
14 regression cases since the 502-test formatting baseline. All four outputs
remain needs_review drafts. Some compound acceptance criteria, broad quality
claims and the known SDLC ranking limitations still require review. The successful
selected runs do not erase earlier failures or establish a universal no-Retry
or worst-case timing guarantee.

## 2026-10-30 - Complete cyber assessments, SDLC evidence and report choice

User scope: improve threats/risks, provide a defensible SDLC, show analysis and
offer IEEE/Normal generation choices; do not run new examples. Read the project
planning/alignment documents and added ADR-0057 before implementation.

Expanded the source-scoped hypothesis catalog and hypothesis-specific proposed
risk reviews. Retain all applicable material threat/risk candidates independently
of model ordering, with truthful deterministic-composition provenance. Keep
ratings/ownership unassessed and source/requirement links intact. A source-linked
service integrity fallback prevents an empty assessment for supported obligations
without a more specific capability match; it does not fabricate authentication.

SDLC policy 2.0 distinguishes explicit delivery evidence from derived security,
operational, integration, sensitive-asset and deployment factors. Store basis,
source IDs and rationale; expose rule-point contributions and unknown constraints.
Model explanation and method-specific workflow compilation preserve exact
requirements, test references, proposed responsibilities and pending human gates.

Added analysis details and IEEE/Normal buttons with per-project local preferences
and correct export links. Both are views of identical canonical content. IEEE
adds threat/risk/lifecycle appendices; saved empty historical sections stay empty
with an honest pending notice. Normal retains all existing 14 sections/editing.
Added NEW-016 and updated architecture, API contract, README and validation notes.

Stabilized the interrupted acceptance-authoring experiment by restoring the prior
source-group batching and preserving stricter source-outcome guards. Updated an
offline fixture to place its observed isolation result before its condition, and
made the final document fixture compile the currently ranked methodology. The
Agile gate regression now explicitly uses its Agile fixture rather than assuming
every input ranks Agile. These changes do not remove validation or rewrite user
requirements.

Checks: 648 backend tests passed (39.88 s); 19 frontend tests passed; Ruff passed;
TypeScript/Vite build passed. Inspected synthetic threat/risk/ranking PDF pages;
both renderers completed. Existing dependency/React fixture warnings remain.
No fresh live-model run or generation timing claim. Verified no active runs and
restarted only the confirmed port-8011 application in the independent Desktop
checkout, with hidden process logs under data/performance-development. The
original NITK checkout was not changed.

## 2026-10-30 - PAM functional false rejection and predicate coverage

Inspected the latest saved failed PAM run b3e07af6-06bb-4c75-9fd3-dc6cfaba8170
and its private inference/validation history. It stopped after about 80 seconds
with FR-006:unrequested_product_logging_use_test_instrumented_state_capture.
The brief explicitly says "should record privileged sessions, log administrative
actions". The recording detector omitted should/base-verb grammar, so source
normalization removed requested logging and both automatic field corrections
hit the same false rejection. The source compiler also combined log with record,
collapsed grant/modify/suspend permissions, and left controls/monitors inflected.

ADR-0058 fixes affirmative recording recognition, including coordinated duties,
while retaining negative/read-existing-log/sign-in guards. Source obligations 1.1
recognize log, modify, suspend, require and control; shared-object permission
operations preserve actor and target. Added operation outcome checks and focused
test-authoring instructions. Prompt 1.34 invalidates incompatible resumed
checkpoints. The adapter/base policy, validation gates, bounded correction limits,
source evidence, review semantics and historical failed run remain intact.

Checks: 664 backend tests passed (42.67 s, 24 existing dependency warnings), Ruff
passed. New cases replay the exact failed recording criterion unchanged, verify
affirmative modals and excluded logging, and exercise actual functional/quality
compilation for the full PAM brief using an inert author with repairs disabled.
All source operations survive the complete validation gates in that offline test.
Frontend unchanged; its tests/build were not repeated. No fresh full live model
generation was started, respecting the earlier no-generation instruction. Offline
tests establish the false-rejection fix, not a measured no-Retry completion rate.

## 2026-10-30 - Two new live examples and Desktop analysis files

Ran the exact backup/recovery and network configuration examples sequentially.
Stopped the initial backup test when inspection found source parser defects:
It became a person, backup-and-restore activities became a restore command, and
define/initiate/submit/track were not independent predicates. ADR-0059 fixes those
cases. Initial corrected generations completed, but content inspection caught
copied alternative object templates and unsupported registry/metadata/session
promises in authored tests. ADR-0060 adds targeted prompts/checks; no criteria
were hand-written or validation disabled to achieve success.

One subsequent configuration run failed because a display check saw initiation
in a trailing condition and rejected an actual observed display result. The saved
correction now passes when observed result and triggering condition are separated;
genuine initiation-only tests remain rejected. Added three explicit regressions.

Final backup run 0620d283-418e-465e-bb00-80142480ff4b completed in 122.919 s;
configuration 769f6745-04ab-4bfb-bffd-82383f3f454d in 97.261 s. Both completed all
14 sections without a user Retry stop, with internal adapter/base corrections
and actual model authorship preserved. Both remain needs_review and neither was
approved. Saved IEEE/Normal PDFs and complete analysis Markdown per project on
Desktop; parent Results and timings.md records earlier stops and exact timings.
Version hashes, original input, export bytes, current validation and per-run
source stability were checked. Visually inspected primary layouts and normal
samples. Detailed authored implementation assumptions remain review items.

Checks: 680 backend tests passed (41.39 s); Ruff passed. Frontend unchanged.
Preserved every attempt under demo/backup-config-20261030. Application stays
running locally on 8011 with prompt 1.37. No scans, restores or actual network
configuration operations were executed; only document generation and tests.

## 2026-10-30 - Two additional examples in the existing Desktop folder

User requested two different examples, results in chat and files in the same
Desktop folder. Selected assistant-written vulnerability-remediation tracking and
digital-certificate management briefs. Generated them sequentially through the
real application; exact briefs, source profiles and every run are retained under
demo/remediation-certificates-20261030.

Remediation completed on its first generation run in 144.075 s (analysis 6.246 s).
Before the certificate run, source inspection identified approve/renew grouped
inside a review row. ADR-0061/source policy 1.3/prompt 1.38 retain independent
approval and renewal obligations with model-authored observed outcomes. No
crypto algorithm, validity period, issuer or additional approval authority was
selected. A test fixture gained the existing close action and correctly places
conditional wording after its observable outcome. Existing source guards remain.

Certificate management completed on its first generation run in 139.617 s
(analysis 6.680 s). Neither run stopped for user Retry; automatic adapter/base
corrections are part of the measured time, and actual model authorship is saved.
Remediation has 5 hypotheses/5 risks and certificates 6/6; both recommend a
provisional Incremental workflow and remain needs_review, with 21/21 checks and
no human approvals. Versions: 7cb4acad-ca11-4602-aac3-ca0492e53a48 and
38e4fbe3-3f2c-46f1-9ed8-6b191603bd1f. Source profiles were stable per run;
remediation used the preceding prompt 1.37 and certificates used 1.38.

Saved IEEE PDFs (17/18 pages), Normal PDFs (41/41 pages), and Project analysis.md
per new project in the existing Desktop parent. A separate Additional examples -
results and timings.md preserves the earlier report and is linked from its index.
Rechecked original briefs, canonical hashes, current quality, absence of reviews,
export bytes and per-run source stability; inspected all primary page overviews
and Normal samples. Analysis notes retain unresolved interface/schema choices.

Checks: 682 backend tests passed (41.41 s, 24 existing dependency warnings); Ruff
passed. Frontend unchanged, so its tests/build were not repeated. These two
measured first-run successes do not establish universal no-Retry behavior or
semantic correctness. No assessment scanning, certificate issuance or external
infrastructure operation was executed; these were document-generation runs.

## 2026-10-30 - API access-management demo recovery

Inspected the exact reported failure with the user's one-hour deadline. Let the
active user retry complete before restarting; it succeeded before the fix and
is recorded separately. Found a missed active denies inflection, corrective code
that kept guessing a response number/lockout, and detection guidance incorrectly
disabled by a separate alert operation in the parent paragraph.

ADR-0062/prompt 1.39 adds active decision forms, per-operation guidance and native
corrective-field bounds. Source-free numeric guesses are excluded when no digits
are supplied; enforce/detect repairs require decision/recognition predicates.
Semantic checks still reject extra responses. Existing field repair limit is
three under the same 120-second deadline, without static default criteria,
omitted requirements, infinite retries or false success. Original evidence and
failed history remain unchanged; actual model authorship is preserved.

Two fresh exact-source runs completed in 125.865/93.730 s, functional sections
52.554/49.046 s, without user Retry stops. Both exported IEEE and Normal PDFs.
Verified original source, hashes, current quality, export bytes and source
stability. Inspected final primary layouts and Normal samples. Saved both PDFs,
analysis and API Access - demo readiness.md in the existing Desktop folder.
Evidence and a real-provider native-schema diagnostic are retained under
demo/api-readiness-20261030. Final version
6b5260de-9c5e-4da7-8a7c-458e6e77a32e remains needs_review; no approval was created.

Checks: 689 backend tests passed (33.03 s), 19 frontend tests passed, Ruff and
production build passed. Existing dependency/React fixture warnings remain.
These measured successes do not establish no-error behavior for every possible
future input or unavailable local-model runtime.

## 2026-10-30 - General observed-outcome recovery and two fresh examples

A new secrets-management project failed after prompt 1.39. Audit history showed
that repair guidance requested inspected content to be returned and permission
state to be updated, while separate validator verb lists rejected those exact
results. An initial shared-map fix exposed a second gap: register was parsed as
an unclassified source behavior, so native repair could repeat an invalid audit-log
result. Both failed runs remain in SQLite and are not reported as successes.

ADR-0063 replaces the drifting lists with one action-to-observed-outcome contract
consumed by validation and every field-local repair schema. All functional parser
verbs are covered by a regression invariant; register/reject/identify are explicit
source actions, and registration repair cannot substitute a new audit record for
the registered object's state. Prompt 1.41 and source-obligations 1.4 invalidate
incompatible checkpoints. Criteria remain model-authored and all existing semantic
and completeness gates remain enabled.

After refreshing port 8011, ran the user's remote-access and security-exception
briefs sequentially, exactly once each. Remote access completed all 14 sections in
114.957 s (functional 42.729 s); security exceptions completed in 116.082 s
(functional 57.520 s). Neither stopped for user Retry. Each is a needs_review
draft with 7 threat hypotheses, 7 linked risks, a provisional Incremental SDLC,
no human review decision, stable source hashes and a 20-page IEEE PDF. Canonical
hashes, original descriptions, all normative PDF statements and absence of reviews
were checked. Analysis Markdown and IEEE PDFs are saved in the new Desktop folder;
run evidence is under demo/remote-exception-20261030.

Checks: 700 backend tests passed in 45.10 s with 24 existing dependency warnings;
Ruff passed. Pytest also emitted the existing Windows temporary-directory cleanup
permission warning after completing successfully. Frontend was unchanged and was
not retested. These two first-run successes demonstrate the measured cases, not a
guarantee against unavailable models, contradictory input or every future brief.
