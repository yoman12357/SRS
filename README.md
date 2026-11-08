# CyberSRS — sequential section agents

An independent local application that turns an informal cybersecurity/networking
description into an evidence-linked SRS and a justified SDLC workflow. Built in
response to the user's sequential-agent design and the professor's brief.

**Status: implemented workflow under live-output correctness repair.** Historical results
under `ai/` belong to the source project and do not validate this new application.

One coordinator runs analysis/clarifications, then specialists for introduction,
functional, non-functional, security/privacy, data, networking/interfaces, compliance applicability,
architecture, threats, risks, stories/use cases, verification, glossary and SDLC,
one at a time through local Ollama. Every output is validated JSON. SQLite stores
checkpoints and immutable documents; a deterministic renderer creates section-wise
PDF/Markdown and a traceability matrix from the same content.

The default reader and PDF/Markdown exports now follow the IEEE 830-1998 outline:
Introduction, Overall description and Specific requirements. Stakeholders use
simple display labels such as User, Admin and Project Analyst; source groups and
their distinct permissions remain visible. The introduction and every canonical
requirement keep their original wording. Full acceptance procedures, architecture,
SDLC and drafting records remain available through **Supporting details & editing**
and the **Full supporting report PDF** link (`detail=full` for exports).
The checked DNS and research-laboratory examples each produce a five-page primary
report, reduced from 26 and 24 pages respectively. Length depends on the supplied
content; requirements are never truncated to meet a page count. See
[format verification](demo/ieee-830-20261029/Formatting%20verification.md).

Requirements retain exact input evidence, citations, priorities, dependencies and
model-authored acceptance criteria. Automated checks catch structural and selected
grounding defects; a human must review semantic correctness and approve the exact
content hash. SDLC scores are deterministic suitability points, not probabilities.

Recognizable independent source predicates now receive separate canonical rows.
Their statements are compiled from the stakeholder's source clauses, with the
local model authoring their acceptance tests. Conditional or ambiguous clauses
stay whole. Source obligations cannot be satisfied by mentioning them only in
test prose. Clarifications share a source-scoped decision inventory; runtime
behavior remains visible under functional requirements. See
[ADR-0056](docs/adr/0056-source-obligations-and-question-boundaries.md).

## Run on another Windows PC

Install 64-bit [Python 3.12](https://www.python.org/downloads/windows/),
[Node.js 24](https://nodejs.org/en/download), and [Ollama for Windows](https://ollama.com/download/windows).
Open Ollama before running setup. Allow about 12 GB of free disk space and an
internet connection for the first setup. Generation and retrieval run locally.

Clone the repository with Git, or extract the source ZIP from the
[CyberSRS release](https://github.com/yoman12357/SRS/releases/tag/v0.1.0).

```powershell
git clone https://github.com/yoman12357/SRS.git
Set-Location SRS
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
.\start.cmd
```

For the ZIP, open PowerShell in the extracted directory and run the last two
commands. Open [CyberSRS](http://127.0.0.1:8010/) after launch. Setup creates
`.env` from the example on a fresh install and respects an existing configuration.
It builds the frontend, verifies and imports the exact released fine-tuned Qwen
weights, installs missing base Qwen and nomic embedding models, and indexes the
starter knowledge. Run setup again to retry an interrupted download.

The release also includes the raw QLoRA adapter for historical asset inspection.
The runtime uses the verified merged Ollama model. See
[model provenance](models/NOTICE.md) and [source asset notes](resources/README.md).
The three [example drafts](demo/one-run-verification-20261108) include the
project briefs, analysis, review questions and IEEE PDFs.

`python -m cybersrs.tools ingest --all` ingests the full local corpus. The default
seed covers authentication, authorization, logging, segmentation and zero trust.
The ingestion manifest records exact source hashes. No application network calls
leave loopback; no telemetry, analytics or user-project training collection.

## Run and check

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run build
Set-Location ..
.\.venv\Scripts\python.exe -m cybersrs
```

Open the loopback application at the backend port configured in `.env`. `start.cmd`
launches the same backend and built React interface. `setup.ps1` prepares an
independent environment on a new machine. For frontend development, run `npm.cmd
run dev` in `frontend/` with the backend running; Vite reads both ports from `.env`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe scripts/audit_assets.py
Set-Location frontend
npm.cmd test
npm.cmd run build
```

The React interface supports project clarification, progress/cancel/retry,
references, version selection, section editing/regeneration, human decisions,
JSON/Markdown/PDF download and local cybersecurity questions. Failed runs retain
validated checkpoints; retries revalidate them and preserve exact source inputs.
Section edits rebuild affected linked artifacts without replacing unrelated
requirement sections. New versions never inherit human approval.

The current performance profile adds live and retained section/total timers,
configurable section budgets, compact source-bound authoring, and exclusive residency
of the configured main-model variants. Two fresh real runs completed all 14
sections in 96.8 seconds (university VPN) and 84.2 seconds (campus access control),
excluding prior analysis and PDF export. Their slowest sections were 22.0 and
27.5 seconds. See [the timing report](demo/final-performance-20261029/Generation%20timing%20report.md).
Both remain drafts requiring human review; these timings do not establish general
semantic correctness. The latest application suite has 516 backend tests passing;
frontend tests/build and sampled PDFs are checked separately in the report.

The current integrated suite passes 516 backend and 16 frontend tests; Ruff and
the frontend production build also pass. Real
testing produced complete drafts, then manual review exposed omitted acceptance
outcomes, narrowed exclusions and architecture entries that only repeated controls.
The current profile repairs one missing model-authored artifact at a time and
requires linked logical components, directed flows and boundary enforcement.
Fresh real cases and complete PDF/output review are still required before this
project can be called complete. See [the roadmap](docs/ROADMAP.md)
and [work log](docs/WORK_LOG.md). API routes are documented in
[API_CONTRACT](docs/API_CONTRACT.md).

The four supplied Wi-Fi, email, endpoint and firewall checks exposed purpose-wording
and source-binding failures. The repaired source-batch-1.3 profile keeps valid groups
frozen and revalidates bounded model-authored corrections. The latest fresh run of
each case completed all 14 sections in 89.649, 55.067, 41.495 and 81.364 seconds,
respectively, without a manual Retry or checkpoint reuse. Earlier failures remain
in the evidence. These drafts and timings do not establish universal one-run
reliability or semantic approval. See
[four-example results](demo/four-examples-20261029/Generation%20results.md).

The matched two-description comparison completed 0/2 adapter-only drafts and 2/2
base-only drafts, but content inspection rejected both completed base drafts.
Current source guards also reject their omitted capabilities, invented numerical
targets and recorded-approval claims. Two assistant-reviewed development examples
are available; their inferred impact labels now fail the stricter source checks.
They do not establish automatic generation correctness or adapter improvement.
See [validation evidence](docs/VALIDATION.md).

The project workspace provides a private history download with source revisions,
exact local model attempts and exported document bytes. This history stays in
SQLite until project deletion and can contain private project inputs. Standalone
chat is ephemeral; project-scoped chat is recorded. The history is not a
tamper-proof ledger, and prompts from older runs are not reconstructed.

Copied datasets, source knowledge and adapter bytes are verified in
`docs/reference/ASSET_MANIFEST.json`. Historical datasets do not fully match these
new schemas and have not been retrained or relabelled. The former project plans
remain under `docs/reference/`. Financial
examples are adapted to cybersecurity; legal/compliance applicability is not
invented. The platform does not implement enterprise authentication/MFA, conduct
human studies, execute security attacks or modify infrastructure.

The configured trained model is asked first. If its output fails validation,
the same approved base Qwen model may correct it under identical checks; configure
this with `CYBERSRS_BASE_REPAIR_ENABLED`. Requested and actual model tags are
visible in the AI drafting record and exports. Mixed correction runs do not prove
adapter improvement. Use pure `--variant base` / `--variant finetuned` evaluation
runs for comparison, and add `--repair` only when evaluating the deployed policy.

After analysis, review the domain, roles, interpreted scope and open decisions,
then choose **Generate IEEE SRS** or **Generate Normal SRS**. IEEE uses the existing
IEEE 830 organization with threat, risk and SDLC appendices. Normal presents all
14 sections and editing tools. Both use the same canonical content; the selected
reader format controls PDF/Markdown exports and is remembered per project on
this browser. Switching formats does not generate again or change approval hashes.

Source-derived advisory 1.1 retains applicable identity, permission, revocation,
administration, integration, audit, monitoring, separation and filtering hypotheses.
Risks include the potential consequence and a proposed assessment/treatment action;
unknown ratings and ownership remain explicit. These are planning hypotheses,
not discovered vulnerabilities or additional approved controls. Historical empty
assessments are displayed honestly and are not silently populated on export.

SDLC policy 2.0 distinguishes explicit delivery evidence from derived security,
integration, operational and deployment suitability. It records source IDs and
rationale, retains unknown delivery constraints, and recommends a methodology
with matching phases and pending human gates. Derived-only recommendations are
provisional. Offline checks cover this change; fresh live-model acceptance was
not run because the user requested implementation without generation. See ADR-0057.

The PAM reliability fix (ADR-0058) preserves explicitly requested session/action
recording and separately compiles permission grants, modifications, suspension
and revocation. Genuine unrequested logging still fails validation. Automatic
correction remains bounded; a saved failed run is not rewritten as successful.
The regression replay and offline full PAM compiler pass, but a fresh live
completion rate has not been measured for this fix.

The API access recovery update (ADR-0062) distinguishes valid access decisions
from invented response-code or lockout guesses. Corrective fields use short,
source-bound native schemas and full validation. Two fresh runs of the user's
API brief completed without a user Retry stop and exported IEEE and Normal PDFs.
See docs/VALIDATION.md and the Desktop API readiness report. These are measured
case results, not an unlimited no-error guarantee for every input or unavailable
local-model runtime.

ADR-0063 removes a broader prompt/validator mismatch by sharing one observed-outcome
contract across semantic validation and native field repair for every recognized
functional action. After the final prompt 1.41 update, the supplied remote-access
and security-exception examples each completed all 14 sections in one generation
run (114.957 and 116.082 seconds) and produced checked 20-page IEEE drafts. Earlier
failed attempts remain in history. See docs/VALIDATION.md; two successful examples
do not make an unlimited no-failure guarantee.
