# ADR-0038: Distinguish existing log records from new event recording

Inspection of the actual rejected profile-1.27 VPN DR-001 found that its deletion
criterion demands a deletion event logged by the system. Its source specifies
retaining connection logs for 14 days and removing expired logs, without requiring
a separate deletion-event log. The logging guard currently returns early whenever
the source contains the noun "logs", so the unsupported new event escapes it.

Retain source-authorized inspection/storage of existing log records and explicit
source requirements to record events. When the source only describes existing
records, distinguish recognized new event-recording assertions from inspection
of those records. Test instrumentation remains allowed. Independently validate
the result and witness; do not rewrite model-authored criteria or manufacture an
audit event as evidence of deletion.

This is a bounded fix to an observed source-validation bypass, not a universal
semantic entailment test. The same rejected criterion also has an incoherent
creation-time step, which this logging distinction alone does not resolve. A
passing section still needs actual content review. Version the quality policy
when integrating; preserve historical content/hashes and failure artifacts.

Implemented as source-grounding-1.4. The initial regression reproduced three
failures; storage inspection, external captures and explicit recording remained
permitted. After the fix, staged checks passed 308 tests and integrated checks
passed 309, including a real section-gate regression. Ruff passed. A real repair
probe now rejects the actual row's logging defect, but whole-row correction still
failed on its separate regulation claim. This source guard is not complete repair
or SRS correctness; the failure remains in data/rationale-repair-probes/20261028-061533.
