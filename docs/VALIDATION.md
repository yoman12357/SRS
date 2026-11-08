# Validation evidence and remaining gates

Updated 2026-10-28. This is the new Desktop implementation; copied historical evaluations
are not evidence that its runtime succeeds.

| Check | Observed result |
| --- | --- |
| Independent Python environment | Python 3.12.10; project dependencies installed locally |
| Reused assets | 789/789 SHA-256 matches, no missing/corrupted files |
| Historical dataset JSON | 519 records in data_test and 519 in data_test2; parses cleanly; not retrained |
| Local retrieval | Six OWASP documents, 111 persisted chunks; private isolation regression passes |
| Backend unit/API/schema | Last integrated run: 428 tests pass, including source fidelity, canonical category indexes, criterion-first repairs, corrective history, record/event-log distinction, typed Agile composition, privacy and V-Model plan links |
| Frontend | 9 tests pass; TypeScript/Vite build and Prettier check pass |
| Python lint | Ruff passes for src/tests/scripts |
| Frontend dependency audit | npm reports zero issues |
| UI inspection | Local landing page renders in app browser, including narrow responsive layout |
| Live trained-model-first policy | Complete campus drafts exist; actual model tags include adapter and base corrections. Current manual review still rejects architecture/scope defects in older profiles |
| Live base comparison | Matched eval-001/eval-006: adapter 0/2 completed, base 2/2 completed; both base drafts rejected on content inspection and current source checks |
| Real output correctness | Not achieved |
| Two correct automatic real cases | Not achieved; two substantially assistant-reviewed development documents exist |
| Real PDF visual review | Earlier draft layouts visually inspected and compacted; final current-profile correctness/layout review remains outstanding |
| Human approval | No real approval requested or fabricated |

Use `scripts/live_check.py --variant finetuned --cases campus vpn` and the identical
`--variant base` cases. Outputs and per-agent model timings go under data/evaluations.
Failed runs may resume with `--resume-dir <that evaluation directory>`; checkpoints
are revalidated under current rules. Do not run competing heavy evaluation processes.

The two authored smoke cases test campus NAC with evolving requirements/Agile and
remote-access VPN with stable requirements and independent verification/V-Model.
They are implementation regressions, not a statistically adequate claim that the
adapter improves the model. Original held-out dataset bytes remain unchanged.

The asset audit now directly validates historical assistant targets against the
current schemas: 0/1,038 conform without adaptation. Historical context/question
tasks now share Analysis, so this is an interface-compatibility result, not a
semantic score. No labels, scenario splits, citations or threat data were invented.

At profile sequential-1.5, the fresh campus run under
`data/evaluations/20261027-072902-finetuned` completed in 417.2 seconds, selected
Agile and stored five canonical requirements. Manual inspection rejected its
conditionalized exclusion and requirement-only architecture entries. Profile
sequential-1.6 adds explicit architecture semantics and exclusion checks; do not
use the older draft's green checks as evidence that the current gates pass.

The same earlier profile also completed VPN in 583.7 seconds and selected V-Model.
Manual review found broadened MFA actor scope, an ambiguous combined permission
statement and generic testing stages rather than explicit V-Model pairings. These
are rejected output defects, not accepted evidence of final correctness. The
current-profile campus UI run is recorded in the app-root database; its ID and
results must be inspected before claiming success. Runtime model digests were
snapshotted locally in data/runtime-models-snapshot.json.

At sequential-1.14 the frozen HTTP evaluation in
`data/http-evaluations/20261027-135650` failed campus at a runtime error and VPN
at an overbroad planning-capacity check. The next frozen profile (1.15) under
`data/http-evaluations/20261027-140711` passed introduction but failed both cases
at an Ollama native-output parser error. Neither produced an accepted document.
The runtime remained reachable. A real retry captured the exact HTTP-500 envelope
privately in `data/runtime-error-probe-1`, without creating a version or approval.
ADR-0019 documents its bounded output-correction classification in profile 1.16.
That new profile is being observed in `data/http-evaluations/20261027-141900`;
inspect its persisted outcome rather than assuming completion from this note.

The source-bound introduction change prevents factual item paraphrases such as
expanding 'No continuous delivery' into 'a fixed release cycle'. Numeric checks
now distinguish registered users from a separately stated concurrent-session
quantity. Functional views index later security-owned actor actions by canonical
ID. A real-schema API regression verifies architecture edits rebuild threats and
risks from the revised design. The final backend suite and Ruff checks pass; these
checks do not establish semantic correctness of live model output.

Earlier PDF template cover, contents and first requirement pages were visually
inspected using an explicitly invalid older draft. Text and contents layout are
readable. This is layout evidence only, not acceptance of that draft or a current
final PDF. At that checkpoint exact request/correction audit history was pending;
the later implementation and real audit inspection are recorded below.

During profile-1.16 review, the source-faithful manual isolation/restoration row
contained only an isolation criterion. The positive-permission guard currently
requires an adjacent denial clause before checking action coverage; it therefore
missed restoration. ADR-0020 records the pending correction. Its system-log
witness also needs review against the narrow policy-change logging scope. Do not
accept this profile solely because its current automated gates pass.

Later verification, profiles 1.18–1.21:

- A matched protocol diagnostic found native-schema parser failures on /api/chat;
  /api/generate produced schema-valid output with the same installed Qwen models.
  Production now uses generate with separate system/prompt fields. Semantic gates
  still apply; other runtime failures remain visible. No model weights changed.
- The real sparse-description HTTP workflow asked three clarification questions.
  Explicit test skips remained unresolved and were not asked again. Its downloaded
  private audit contains exact request/response/validation and source revisions;
  payload hashes were verified. No SRS or human approval was created by this check.
- Profile 1.19 VPN completed, selected V-Model and exported a 33-page PDF under
  data/http-evaluations/20261027-152129. Assistant inspection rejected missing
  25-session capacity, broadened MFA scope and absent explicit V-Model planning/test
  pairs. This is a rejected draft, not semantic acceptance or human approval.
- Profile 1.20 frozen cases under data/http-evaluations/20261027-163122 both
  failed permission-test checks. Inspection found false rejections of successful
  internet access qualified by no error, and a returned log view implementing
  inspection. Profile 1.21 corrects those cases with positive/negative regressions.
- Current backend suite at profile 1.21: 156 passed, 24 third-party deprecation warnings. Ruff
  lint and formatting pass. Latest frontend suite: 7 passed; build/Prettier pass.
  Asset audit refreshed at profile 1.21: 789 hashes match; historical schema
  compatibility remains 0/1,038 and no training or split changes occurred.
- Fresh frozen 1.21 HTTP evaluation: data/http-evaluations/20261027-164444.
  Its actual outcome and source-by-source review remain pending.

That 1.21 evaluation subsequently failed both cases with an unchanged source
snapshot: campus at architecture logging/retention scope and VPN at duplicated
copied requirements in the exclusion passage. Profile 1.22 integrates ADR-0025
with 176 passing backend tests and passing Ruff lint/format. Its fresh frozen
evaluation is data/http-evaluations/20261027-171155; actual completion and semantic
review remain pending. The manual retention policy and unimplemented automatic
PII masking are recorded explicitly in DATA_HANDLING.md.

Profile 1.22 was interrupted to correct a false rejection of the explicit witness
"test instrumented log". Cooperative cancellation completed, no VPN case was
started, and its source snapshot matched at interruption. Profile 1.23 accepts
that wording while retaining the production-log rejection regressions. Current
backend checks: 178 passed, 24 third-party warnings; Ruff lint/format pass.
Fresh frozen HTTP evaluation: data/http-evaluations/20261027-171656. No accepted
current-profile document or human approval is claimed yet.

The 1.23 cases both terminated failed with unchanged source snapshots. Campus had
a false architecture logging match on "logical" and a genuine unsupported waiting
period in a partial restoration test; VPN added an unsupported exclusive-role
test while completing administrator management. Assistant reviews are saved with
that evaluation. Profile 1.24 integrates the corrections in ADR-0026: 192 backend
tests pass, 24 third-party warnings, final Ruff lint/format pass. Fresh frozen
evaluation: data/http-evaluations/20261027-174444; actual outcomes and full review
remain pending.

Later profile 1.24 also terminated failed with unchanged source snapshots: campus
misclassified sign-in as event logging and had collapsed trust-domain endpoints;
VPN falsely rejected opening a log dashboard and receiving its data. Profile 1.25
integrates ADR-0027, with 213 backend tests and final Ruff lint/format passing.
Fresh evaluation: data/http-evaluations/20261027-181046. Campus uses the retry
endpoint, but profile mismatch invalidates prior checkpoints and rebuilds sections
from saved input. The comparison and real final-document review remain pending.

## Current evidence: 2026-10-28

The matched comparison in `data/heldout-comparisons/20261028-005129` retained
unchanged production snapshots, dataset bytes and installed model digests. It used
the original eval-001/eval-006 descriptions, identical inference settings and no
cross-model correction. Adapter-only failed both cases (invalid dimension and
truncated/repetitive output); base-only completed both but inspection rejected
missing firewall/monitoring behavior, invented quantities and approval claims.
No missing SDLC gold labels or stakeholder answers were fabricated. During that
run, a few interactive metadata edits performed local retrieval embeddings; no
other text generation was started. Times are observational, not an uncontended
performance benchmark. These descriptions have now been inspected and cannot be
presented as fresh unseen cases for later tuning.

A separate local-model review experiment at
`data/source-review-probes/20261028-012852` missed all four inspected bad sections
and produced six spurious issues for a reviewed SDLC control. It is not adopted
as a gate or a confidence measure; its negative evidence is preserved.

ADR-0032 adds source-grounding policy `source-grounding-1.1`, independent of the
generation prompt. Recognized durations/percentages/throughput, descriptive fields,
linked acceptance logging, recorded-approval claims and actual storage-lifecycle
outcomes are now checked. Current revalidation rejects both completed base drafts
without changing their historical content hashes. Evidence is in
`data/source-grounding-reviews/20261028-042353/report.json`.

Campus version 19 (`4627d563e032674b003c52eb8768eaf603a708e292c3fa9e19a6b532275b0906`)
and VPN version 17 (`1519fcbea4cb7052e7473b638c89d6d16d89a9e0d5ba8d31bd6709c68626857f`)
pass the current guards. They contain substantial explicit assistant revisions;
they are development examples, not automatic-generation successes or human
approvals. Re-exported PDFs have 29 and 36 pages with no blank pages. Selected
actual cover, contents, requirement, SDLC and traceability pages were inspected;
the source matrix and visual scope are recorded beside those exports.

The real privacy repeat probe in
`data/boundary-evaluations/20261028-003821/privacy-repeat.json` confirms the
fictional email was masked in the actual request and restored locally. The first
probe exposed a punctuation bug and remains preserved. The contradiction probe
in the same directory surfaced opposing permission statements in a critical
clarification; it did not fabricate an answer or approval. Masking limitations
remain documented in DATA_HANDLING.md.

Current checks: 265 backend tests passed (24 third-party deprecation warnings),
8 frontend tests passed, TypeScript/Vite build passed, Ruff and Prettier passed.
Pytest's default temporary-directory cleanup reported a Windows permission
warning after successful execution; no test failure was hidden. The attempted
`npm run format:check` command is unavailable; the installed Prettier CLI check
was run successfully instead.

Fresh trained-first development regression:
`data/evaluations/20261028-042259-finetuned`. Real Ollama, reported base correction,
no assistant edits, no invented answers and no approval. Inspect its terminal
result/source stability before drawing conclusions. Automatic SRS/SDLC correctness
remains unproven.

## Integrated profile 1.27 / source-grounding-1.2

The 04:22:59 trained-first run has terminated with both cases failed: campus at
functional linked-test repair after 336.2 seconds; VPN at verification on
TEST-010's invented numerical commitment after 1231.9 seconds. The terminal
stability file confirms unchanged production source. Inspection of VPN's accepted
intermediate checkpoints found post-subject concurrent inventory misuse, invented
session rejection caps, mutual authentication, unnamed privacy-regulation claims,
UI-message commitments and unsupported risk labels. It was not a correct SRS.

ADR-0033 implements source-owned linked-test vocabularies and parser checks,
narrow linked-criterion repair, additive named-capability completion, observable
denial prompting, and guards for those observed source violations. Missing
likelihood/impact ratings remain unknown; explicit source assessments are
preserved. Main full suite: 285 passed, 24 third-party warnings; Ruff passed.
Using a fresh workspace-local pytest base directory avoided the unrelated Windows
temporary-directory cleanup warning. Frontend remains 8 passed/build/Prettier
passed with no subsequent frontend code changes.

This stricter policy also rejects the three campus and five VPN inferred impact
labels in the explicitly reviewed example versions. Their policy-1.1 results,
content hashes, PDFs and selected-page inspections remain historical evidence;
the examples have not been silently rewritten or exempted. Current findings are
saved in `data/source-grounding-reviews/20261028-042353/policy-1.2-review.json`.

Fresh real profile-1.27 regression:
`data/evaluations/20261028-045259-finetuned`, adapter-first with reported base
correction and no assistant edits/answers/approvals. The run terminated with
unchanged source: campus completed in 945.8 seconds; VPN failed in 796.9 seconds
on DR-001's unsupported privacy-regulation claim. Assistant content review rejects
the campus draft despite its expected Agile label: invented empty-category prose,
missing logical network domains, unsupported scenario/logging conditions,
irrelevant guidance citations and a linear lifecycle with unconfirmed delivery
roles. See `campus-assistant-review.json` in that evaluation directory. Completion
of generation is not correctness or human approval.

The React document badge now explicitly says "Invalid draft · validation failed"
when current source checks fail, even if a historical review approved that exact
content. This matches the existing server/export approval boundary. Frontend:
9 tests passed; TypeScript/Vite build and Prettier passed. Actual browser proof:
`data/source-grounding-reviews/20261028-042353/ui-invalid-policy-1.2.png`.
The live API reports policy 1.2, the unchanged campus/v19 hash, three unsupported
impact-label errors and zero human reviews. This UI check started no generation.

## Bounded composition and correction follow-up

ADRs 0034–0037 add factual no-gap category indexes, typed iterative SDLC phases,
source-confirmed or visibly proposed delivery roles, rationale-only correction,
and accumulated bounded corrective history. Main suite: 301 passed, 24
third-party deprecation warnings; Ruff passed. Frontend remains 9 passed with the
previous successful build/Prettier checks; it was not changed by this work.

The first real focused probe, `data/category-lifecycle-probes/20261028-053155`,
retained unchanged source/input. It exposed missing category IDs and SDLC retry
regression: a middle candidate had iteration but other defects; the final one
forgot the iteration correction. It failed, rather than establishing SDLC quality.
The second probe in `data/category-lifecycle-probes/20261028-060409` uses the exact
production category gate and compact verification context. Its category output
includes known network controls on the first adapter attempt. SDLC failed after
368.6 seconds despite actual retained diagnostics/candidate context. The model
renamed verification as iteration without adding implementation or a return path.
Neither probe is a complete SRS, fresh held-out evaluation or approval.

The real rationale-only probe `data/rationale-repair-probes/20261028-061325`
changed exactly DR-001's rationale in 15.1 seconds and left its other fields
unchanged. Assistant inspection rejected the unchanged deletion-event log and
incoherent temporal step. Source-grounding 1.4 closes that logging bypass without
forbidding stored-log inspection or test captures. The next real probe,
`data/rationale-repair-probes/20261028-061533`, failed after 52.7 seconds on the
regulation claim during whole-row correction. Both have source stability true;
neither proves a correct data section. Criterion-first repair is staged.

SDLC generation 1.5 (ADR-0039) composes an internal typed Agile cycle into the
unchanged public phases. Integrated checks: 318 passed, 24 third-party warnings;
Ruff passed. Actual probe `data/category-lifecycle-probes/20261028-062008` is
running. It reuses automatic requirements, with no assistant section edits or
human decision. No semantic success is inferred from the software checks.

The typed 1.5 probe above terminated failed after 341.4 seconds on an overly
strict per-action pattern, despite an actual backlog return elsewhere in the
list. Version 1.6 retains complete-cycle validation while permitting additional
refinements. Criterion-first repair is integrated. Final integrated checks:
320 passed, 24 third-party warnings; Ruff passed.

At the user's request, a fresh full base-only evaluation is running under
`data/evaluations/20261028-072314-base`. It uses the normal local Qwen tag directly,
with no adapter/fallback, assistant section edits or invented answers. Source is
frozen; a content/PDF verdict must follow the terminal results. The configured
application default has not changed.

The requested base-only run terminated: **0/2 completed**, no SRS versions or
human reviews. Campus failed after 180.7s on an acknowledgement test with no
explicit acknowledgement action in WHEN; rejected drafts additionally invented
audit logging and denial-message behavior. VPN failed after 101.4s because the
introduction turned 250 registered-user planning inventory into "up to 250 users".
Assistant inspection confirms those source defects. All 20 text requests used
only qwen3:4b-instruct-2507-q4_K_M; adapter calls were zero. Terminal source
stability and an independent post-run source comparison are true. Details:
`data/evaluations/20261028-072314-base/assistant-verdict.json`. No completed SDLC
or PDF existed for review. This two-case result does not establish universal
model inability, but it does not justify a base-only default on correctness
grounds. The application default remains unchanged.

ADRs 0040?0043 are integrated: source-bound permission actions, canonical criterion
verification views, per-action exclusions, and exact source-fact introductions.
Current main suite: 353 passed, 24 third-party warnings; Ruff passed. Frontend was
unchanged (previous 9 passed/build/Prettier). The frozen 075702 trained-first run
failed both cases (campus 318.2s compound exclusion, VPN 183.3s introductory cap).
The two subsequent narrow real probes succeeded: eight exact criteria classified
in 4.9s on one adapter attempt; the actual rejected exclusion row repaired in
two adapter calls/11.2s with normative metadata unchanged. Neither is a completed
SRS. Bounded reviews and source stability are saved beside those probe results.

Fresh complete-workflow verification under source-grounding 1.8 and independent
projection versions: `data/evaluations/20261028-090128-finetuned`. Actual handle
96695 is running. No completed document/SDLC/PDF correctness claim is made yet.

The 090128 driver is terminal: both cases failed before introduction inference on
a native-schema KeyError. After the schema-kind fix, a separate read-only backup
retry (090700-finetuned-native-fix) completed both exact introductions but failed
in functional requirements (campus 99.4s; VPN 803.1s). No new full documents exist.

ADR-0044 is integrated; the full suite passed 362 tests including failed passage
call counts. Actual campus witness probe 101155 completed on one adapter call,
but upstream authentication assumptions remain. VPN repair probe 101211 passed
selected gates and was rejected by assistant inspection for invented group,
operation, database and audit-trail commitments. ADR-0045 adds bounded management
scope and existing-log-class checks; the first full run failed three old fixture
statements under the new exact completion contract. Updated those fixtures and
retained their coverage/target checks; final full suite 365 passed, 24 third-party
warnings, Ruff passed. Frontend unchanged (previous 9 passed/build/Prettier).
Real ADR-0045 verification is pending; no human approvals were recorded.

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


## Teacher-demo prototype delivery, 2026-10-29

A verified Campus prototype is available in demo/ and the app at loopback8011.
The 31-page exported PDF, JSON/Markdown, exact content hash, five canonical source
constraints, correct Agile evidence/cycle and no-human-approval state were checked.
428backend tests and9frontend tests pass; Ruff/build pass. Source-linked views and
process compilation fix the major previous scenario/SDLC/automation inventions.
Remaining acceptance assumptions are documented in the exact-hash assistant review.
This delivers the requested rough teacher demonstration, not all Roadmap gates.

The final VPN retry53427560 fails with unconfirmed management creation/removal,
database and production-log witness claims. No PDF or correctness claim is made
for that case. Its source profile remained unchanged through the terminal result.
General automatic output correctness, two correct workflows, calibration and
adapter-improvement claims remain unproven.


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

## Cyber assessments and report choices - 2026-10-30

ADR-0057 was implemented without a fresh live Ollama analysis/generation, as the
user requested. Current checks: **648 backend tests passed** (39.88 s, 24 existing
dependency deprecation warnings), **19 frontend tests passed**, Ruff passed, and
TypeScript/Vite production build passed. The frontend suite retains an existing
React key warning in its invalid-review fixture; it does not fail the suite.

New offline regressions cover should-style campus access/email/endpoint/firewall
briefs, applicable complete source-linked hypotheses and one corresponding risk
per threat, unassessed likelihood/impact/owner, exclusions, no invented identity
feature in the generic fallback, and retention of material assessments despite an
empty/subset model ordering. SDLC tests cover differentiated derived suitability,
explicit verification evidence, sensitive research assets, preserved source IDs,
and unknown cadence/budget/schedule/regulation. Frontend checks exercise both
generation choices, unsupported-domain disabling, remembered format and matching
PDF/Markdown links while JSON remains canonical. Existing mocked API/worker tests
also pass; these are not fresh live-model runs.

Synthetic fixtures render IEEE and Normal PDFs (13 and 17 pages respectively).
Threat, risk and ranking pages were inspected: wrapped text, readable hypotheses,
proposed treatments, unknown ratings, source/requirement references and draft
footers are visible. The IEEE ranking uses a short table plus separate reasons
to avoid a tall unsplittable table cell. Offline inspection files are under
`data/offline-feature-check-20261030`; they are synthetic, not new demo results.

The idle site was restarted to load this implementation. Historical canonical
versions are preserved, including empty historical assessments. No automated
test, synthetic fixture or restart records human approval. Fresh semantic
acceptance, end-to-end live-model timing and a no-Retry guarantee remain unverified.

## PAM functional-requirement reliability - 2026-10-30

The latest user PAM failure was a false rejection of explicitly requested session
recording and administrative action logging. Saved private output showed two
field corrections repeated the same unrequested-logging error. ADR-0058 fixes
affirmative should/shall/must and active/coordinated recording predicates;
negated logging, sign-in and inspection/retention of existing records still do
not authorize new event recording. Source predicate coverage now separates
permission grant, modify, suspend and revoke, plus record/log and control/monitor.

664 backend tests passed (42.67 s, 24 existing dependency warnings); Ruff passed.
The exact saved false-rejected criterion is accepted unchanged. A full PAM
functional/nonfunctional offline compiler test passes actual schema and semantic
gates with automatic test repairs disabled; this uses an inert author, not Qwen.
No new full live model run was started. This fixes the identified causes and
preserves automatic field correction for genuine mistakes, but is not evidence
that arbitrary descriptions always complete without Retry.

## Backup and configuration live examples - 2026-10-30

Generated the exact two supplied briefs sequentially through the real local API.
Analysis took 23.746 s for backup and 7.169 s for configuration; it was reused
for later development runs. Final measured generation took **122.919 s** for
backup (functional 52.273 s) and **97.261 s** for configuration (functional
50.089 s). Both final runs completed all 14 sections without a user Retry stop.
Both are needs_review drafts with 21/21 automated checks and no recorded human
decision. Requested adapter and actual adapter/base corrections are retained.

History was not erased: the first backup attempt was agent-cancelled at 42.088 s
after observing incorrect source clauses; intermediate drafts completed at
135.443/123.555 s but manual inspection found copied template/implementation
wording. A later configuration run failed at 64.009 s because the new display
guard falsely rejected a valid result with a trailing initiation condition.
ADRs 0059-0060 and exact-phrase regressions address these issues. The final backup
used prompt 1.36; configuration used 1.37 after the false-rejection fix. Source
hashes are stable within each selected run, not claimed identical across fixes.

Final versions are 73ef7ad9-6e8e-43df-95ef-ade4fdb20d69 and
c58fca98-9b72-49dc-b101-775a09e7873e. Backup has 6 hypotheses/6 linked risks;
configuration has 5/5. Both select a provisional Incremental workflow with
planning, delivery cycle and handoff, evidence/ranking, proposed roles and pending
human gates. IEEE PDFs are 18/17 pages; Normal PDFs are 38/36 pages. Inspected
all primary pages in overview and normal/detail samples; both styles retain
canonical requirement statements, original inputs and hashes. Detailed authored
acceptance/interface assumptions still require human review; a passed guard is
not semantic correctness proof.

Saved both PDF styles and Project analysis.md in each project's Desktop folder,
plus Results and timings.md under CyberSRS - Backup and Configuration - 30 Oct
2026. Exact inputs, every run, versions, source profiles and page images are in
demo/backup-config-20261030. Final assembly rechecks current version quality,
canonical hashes and exported bytes. Checks: **680 backend tests passed**
(41.39 s, 24 existing dependency warnings), Ruff passed for src/tests/drivers.
Frontend unchanged and not retested. These measured successes do not establish
a universal no-Retry or timing guarantee.

## Additional remediation/certificate examples - 2026-10-30

Ran two new assistant-written briefs sequentially at the user's request, using
the existing local API and model policy. Vulnerability-remediation tracking:
analysis 6.246 s, generation 144.075 s, first run completed. Certificate management:
analysis 6.680 s, generation 139.617 s, first run completed. Neither required a
user Retry stop; internal corrective calls are included in generation timing.

Source preflight before certificates found approval/renewal inside a compound
review row. ADR-0061 separates those explicit predicates and observed tests;
the actual output retains separate review, approval, renewal, revocation and
status requirements. Remediation was generated under prompt 1.37; certificate
management under 1.38/source policy 1.3. Source profiles remained stable within
each run. 682 backend tests passed (41.41 s); Ruff passed. Frontend unchanged.

Current versions 7cb4acad-ca11-4602-aac3-ca0492e53a48 and
38e4fbe3-3f2c-46f1-9ed8-6b191603bd1f both have 21/21 automated checks, needs_review
status, an Incremental workflow, and no human decisions. Threat/risk counts are
5/5 and 6/6. Primary PDFs (17/18 pages) were inspected in overview and normal
report samples (41 pages each) checked. Both export styles preserve canonical
statements and hashes. Interface/field assumptions remain human review items.

Artifacts, analysis Markdown and a separate additional-results summary are in
the existing Desktop folder, without replacing earlier project outputs. Exact
inputs and evidence are under demo/remediation-certificates-20261030. These are
two measured smoke tests, not an adapter benchmark or general reliability proof.

## API access-management recovery - 2026-10-30

Exact project: c13979ef-bf80-4f30-a09b-58c4969f2c2e. Original run
f25effd2-6377-4993-9999-e0cb39d89134 failed at 41.177 s, before its 120-second
section deadline. Corrections repeated HTTP status 403 and account lockout absent
from source. Valid active denies wording was also missed; detection guidance was
omitted when the same paragraph separately requested alerts. The user's later
retry completed before this fix and was not counted as post-fix evidence.

ADR-0062/prompt 1.39 fixes those paths and adds constrained short-field repairs.
Existing automatic repairs are configured to three under the same deadline;
no source/completeness gate was disabled. A separate real base-Qwen provider
diagnostic passed the native constraints; it was not an SRS or human approval.

| Fresh run | Generation | Functional section | User Retry stop |
| --- | ---: | ---: | --- |
| 0ee8b869-7c69-4421-b2a9-c0686f8b66cb | 125.865 s | 52.554 s | None |
| 80b31ca2-1868-46dd-bd6a-13a4fc120220 | 93.730 s | 49.046 s | None |

Both runs completed all 14 sections and exported both report formats. Verified
original source, stable per-run profiles, canonical hashes, current quality and
exported bytes. Final version 6b5260de-9c5e-4da7-8a7c-458e6e77a32e has 21/21
checks, 7 hypotheses/7 risks, an Incremental workflow and needs_review status.
No human approval was recorded. Inspected 20 primary page overviews and a Normal
sample (38 pages). Authored design/test assumptions still require review.

689 backend tests passed (33.03 s, 24 existing dependency warnings), 19 frontend
tests passed, Ruff and production build passed. The frontend's existing React
key warning remains in its invalid-review fixture. Evidence is under
demo/api-readiness-20261030. PDFs, analysis and readiness report are saved in the
existing Desktop results folder. These results verify this measured case, not
arbitrary future inputs, contradictory briefs or unavailable models.

## Shared outcome-contract verification - 2026-10-30

The secrets-management run 58b09bf1-d082-4adb-bebc-7c62e2fed1f1 failed because
inspection/assignment wording requested by the repair prompt was absent from the
validator's outcome vocabulary. The first live check after centralizing those
rules, a3bb263e-ac43-48b2-89a3-4076e8cb3ac0, exposed an unclassified registration
action that could still repeat an invalid audit-log result. Both are retained as
failed evidence. ADR-0063/source-obligations 1.4/prompt 1.41 covers every functional
parser action and constrains validation and native field repair from the same map.

Fresh live results after the final change:

| Example | Analysis | Generation | Functional | User Retry stop | IEEE pages |
| --- | ---: | ---: | ---: | --- | ---: |
| Remote access management | 13.994 s | 114.957 s | 42.729 s | None | 20 |
| Security exception management | 15.024 s | 116.082 s | 57.520 s | None | 20 |

Runs 414541ae-c5c4-4315-997d-36b241a3feb0 and
712f908d-0417-4727-ad4e-9ac9eadbd765 completed all 14 sections on their first
generation attempt. Both source profiles stayed unchanged, prompt 1.41 was loaded,
canonical hashes and original briefs matched, all canonical requirement statements
were found in the IEEE exports, and review lists were empty. Both drafts remain
needs_review with 7 threats/7 risks and provisional Incremental recommendations.

700 backend tests passed in 45.10 s; Ruff passed. The 24 dependency warnings and
post-test Windows temp cleanup warning are recorded. Frontend was unchanged. This
is live acceptance evidence for two supplied cases, not universal semantic proof.

## One-request generation recovery — 2026-11-08

The reported guest Wi-Fi run exhausted compact correction after mixing an access
boundary, open policy decisions and unsupported acceptance details. Compact
generation now uses the configured repair limit inside the existing section
deadline and revalidates the merged candidate on each attempt. Paired access
boundaries require both destinations in normative statements and separate
observations. The validator recognizes a singular instance of a plural destination
and an explicitly required session disconnection. Standalone project goals and
open review instructions stay in the introduction. Spelled-out failed-authentication
counts need source evidence. Repeated identical alternate-flow keys are normalized
before scenario validation, and nested audit-log permissions retain their exact role.

Each recorded successful run made one Generate request to an isolated local
CyberSRS HTTP instance backed by Ollama. These were sequential checks. Earlier
development attempts were retained separately.

| Brief | Prompt profile | Generation seconds | IEEE pages |
| --- | --- | ---: | ---: |
| Conference media room access | sequential-1.46 | 72.358 | 12 |
| Archive recovery console | sequential-1.43 | 74.187 | 12 |
| Laboratory login monitoring | sequential-1.44 | 68.209 | 13 |
| Reported guest Wi-Fi brief | sequential-1.47 | 150.169 | 18 |

All completed the 14 sections and exported the stored requirements with exact
content hashes. The three new examples were revalidated under the final policy.
The PDFs are drafts pending human review. The original guest Wi-Fi rerun was
`c46f55d1-5c10-4e65-bf4e-a698496aac7a`. The three example packages contain the
original input and analysis, the app's open decisions and separately labelled
review questions. The conference PDF has a sparsely filled contents page.

708 backend tests passed with 24 dependency warnings. Ruff passed. These
measurements cover the listed inputs and configuration.

## Reviewed IEEE demo workflow — 2026-11-08

Each successful local Ollama check used analysis, explicit review and one
Generate request. The generation budget was 480 seconds even with a longer
legacy setting. The recovery console submitted a confirmed 90-day retention
answer with Generate. Its answer analysis ran within that same timer, and the
final SRS retained the answer and verification outcome. An earlier attempt
exposed loss of the question context during final consolidation. The regression
now checks the consolidated introduction against its exact source projection.
The certificate inventory rerun preserved exclusive auditor access and kept the
project-design request in the scope section.

| Brief | Generation seconds | Final IEEE pages |
| --- | ---: | ---: |
| Research repository access | 91.592 | 11 |
| Campus certificate inventory | 90.872 | 11 |
| Laboratory recovery console | 76.171 | 11 |
| Reported guest Wi-Fi brief | 158.939 | 18 |

Each export retained the canonical requirement statements and expected test
outcomes. The browser check covered analysis review, both guest Wi-Fi
clarifications, the single IEEE Generate action, and the report and PDF link.
A provider-failure fixture confirmed recovery in the same run without a second
Generate request. The durations describe these local runs. An exhausted deadline
or unavailable model still ends the run with an explicit incomplete status.

714 backend tests and 17 frontend tests passed, along with Ruff and the production
build. The backend reported 24 dependency deprecation warnings.
