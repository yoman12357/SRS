# ADR-0041: Generate verification classifications over canonical acceptance views

The completed profile-1.27 campus draft freely rewrote acceptance into larger
verification tests. Model paraphrases can add product log fields, combine distinct
actions, change retention observations and lose individual criteria. Requirements
and their authored acceptance criteria are the canonical behavioral contract.

The verification specialist still asks the trained local model, but its internal
response chooses test classifications for every existing criterion. Supply the
complete criterion inventory, including linked category criteria, with stable
local keys. Bind key/type choices in the native schema and reject duplicate,
unknown or omitted keys independently. No arbitrary test count cap is introduced.

Compose the public verification plan from those classifications and the exact
authored GIVEN/WHEN/THEN/evidence strings. Preserve every criterion in a distinct
test, in canonical order, without re-authoring its behavior. State explicitly that
the recommended tests have not been executed. Run normal source/link validation
on the composed result. This preserves existing acceptance; it cannot establish
that upstream criteria are correct or adequately specified.

Version automatic projection provenance separately. On unchanged-input retry,
refresh legacy verification and its dependent SDLC without redrafting valid
requirements or earlier artifacts. Canonical edits already rebuild dependencies.
Retain old provenance for unrelated revisions; explicit verification edits remain
source-validated reviewed content and must not falsely claim automatic projection.
Current quality checks independently detect changes to an automatically projected
plan. Historical content/hashes remain immutable.

The existing public test shape, API endpoints and PDF layout remain compatible;
only optional document provenance is added. No model/provider/framework/training
change or human approval is introduced. Work is staged while the real full run
retains frozen production source.

Implemented as canonical-criteria-verification-1.1. Staged and integrated checks
initially passed 334 tests. Real adapter probes preserved all eight automatic
campus criteria, but exposed an exclusion labelled boundary and a noun-success
ambiguity in the shared outcome oracle. Added source/outcome and quantified-edge
constraints and corrected the noun match; regressions retained complete source
coverage and valid positive acknowledgement with unchanged policy.

The final real probe, data/verification-probes/20261028-084438, used one trained
adapter attempt in 4.9 seconds, no base correction, all eight exact criteria and
appropriate positive/negative/inspection labels. Source/input stability is true.
It is a preservation/classification result; retained upstream audit-field and
retention-procedure assumptions still require review. Later integrated suite with
source-action repair: 342 tests passed, Ruff passed. No full-SRS success or human
approval follows from this section result.
