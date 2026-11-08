# ADR-0063: Shared observed-outcome contract

## Status

Accepted

## Context

Acceptance-test guidance and semantic validation separately described valid
operation outcomes. They drifted: repair guidance asked for inspected content to
be returned and permission state to be updated, while the validator rejected
those same externally observable results. Repeating a corrective prompt could
therefore never make progress and surfaced a manual Retry even with section time
remaining.

## Decision

Maintain one versioned action-to-outcome predicate contract in
`source_obligations.py`. Semantic validation and every field-local native repair
schema consume that same contract. The schema continues to prohibit source-free
numbers and the existing full validator still checks target binding, unsupported
fields, implementation promises, logging side effects and source fidelity.

The compact prompt version becomes `sequential-1.41` and the source-obligation
contract becomes `source-obligations-1.4`, so incompatible saved checkpoints are
not silently reused.

## Consequences

- A semantically valid observation is not rejected because prompt and validator
  use different verb lists.
- Invalid corrective output is constrained before it reaches the Python
  validator for every recognized action, rather than only detection and access
  enforcement.
- Criteria remain model-authored. The coordinator does not fabricate a passing
  test or bypass validation when the model cannot produce one.
