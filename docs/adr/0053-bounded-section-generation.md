# ADR-0053: Bounded section generation and measured progress

The user reports Functional Requirements remaining busy for fifteen minutes and
requests successful generation at about 30–60 seconds per section, a visible
section timer, and measured real runs. A failed run is not a completed SRS.

Inspection found repeated full-passage semantic retries, redundant normative RAG
queries whose chunks were never supplied to those authors, and both configured
4B models retained by Ollama. `/api/ps` showed the base model on GPU and the
adapter model with `size_vram=0`; the latter's larger probe generated about nine
stream chunks per second. Context/model residency must be measured, not assumed.

Use a configurable section wall-clock budget (60 seconds in this installation),
including corrective calls. Stream local generation privately, check cancellation
and enforce an absolute async transport deadline even during a silent socket read.
Waiting for the local inference lock and optional retrieval also consumes the
section budget. Close the response when the single requested
JSON value is complete. A complete value still passes the Pydantic and
semantic gates. No partial/prose/malformed output is repaired or rendered as a
completed document. Audit actual streamed chunks and the client completion reason.

Before inference, release only the other configured main-model variant. If that
variant stranded the requested model partly/on CPU, reload the requested model
after releasing it. Never unload unrelated user models. Keep configured adapter
first, with the actual base model used for correction and its authorship recorded.
An already rejected base author's small test correction can continue on that same
model, avoiding another pair of model reloads. This is not adapter-only inference.

The opt-in compact requirement path authors one source-ID keyed group per
uncovered passage in a single section call. The model authors statements and all
GWT test fields. The coordinator supplies IDs, literal evidence bindings,
source-modal priority, explanatory basis metadata and category indexes. Distinct
source actions remain represented in the canonical statements. Clause-level test
coverage and semantic correctness still require human review.
No requirement quota, source truncation or fabricated test result is permitted.
Rejected tests may receive one typed field-local correction; valid siblings and
statements remain frozen, and the full section must validate again. RAG remains
available for advisory sections; retrieved guidance does not create stakeholder
obligations. Empty covered categories are deterministic canonical indexes.

This Qwen installation also supports an explicit raw ChatML encoding option for
the same provider endpoint and schema. Source JSON escapes angle brackets before
insertion so source text cannot close the trusted message boundaries. Public
canonical document schemas and historical versions remain unchanged.

The UI computes live and finished section times from persisted UTC events. Retry
timing starts a new run; reused checkpoints are labelled reused. Failed/cancelled
timers freeze at the terminal run timestamp. Completed times remain visible.

The budget bounds waiting; it does not prove a successful report within that time
on arbitrary hardware/input sizes. Real full-run evidence must establish the
performance claim for the tested cases, and failures remain visible failures.

Status: accepted for the measured performance profile. See
`demo/final-performance-20261029/Generation timing report.md` for two fresh,
completed runs and their full section timings. Broader semantic/research gates
remain open in the Roadmap.

Narrow source-outcome normalization retains authored clauses while removing an
unrequested immediate/instantaneous modifier or a trailing conjunction that adds
new event logging. It never invents an expected result or substitutes a witness;
raw/normalized fields are audited and the full semantic gate runs again. A stated
logging obligation is preserved. Detection alone still cannot authorize account
lockout, isolation or session termination. Model-authored corrections replace
remaining rejected fields, using the original source and frozen valid fields;
invented numeric fixture conditions must also be re-authored as unresolved
parameters. Negated logging reliance and negated termination must not be mistaken
for assertions that those events occur. Source `should` is a normative modal,
and a system-name noun such as 'remote-access management system' is not a new
management operation. Public requirement/test schemas remain compatible.

Architecture native output now constrains internal pairs and their exact allowed
requirement IDs together. Shared source duties may be assigned to more than one
existing component, consistent with the existing shared-ownership design; every
missing obligation must be covered and duplicate identical links remain rejected.
The later routing choice still selects one responsible request/decision owner.


2026-10-29 repair refinement: unsupported numeric specificity is a repairable
acceptance defect. Witness-only errors freeze valid outcomes and let the model
select a schema-constrained external response/state/result capture label. These
are test-instrumentation labels, not asserted product logs. Behavioral clauses
remain authored and the full original validation still applies. No public shape
or local provider changes. The laboratory fresh run completed in 104.151 s; see
demo/research-labs-20261029/Generation result.md for evidence and review limits.
