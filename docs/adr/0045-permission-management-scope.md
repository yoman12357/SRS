# ADR-0045: Keep permission management within its stated scope

Actual VPN repair probe 20261028-101211 passed selected gates but added creation,
revocation, group permissions, a database and administrator audit logging. Its
source says administrators manage remote-access permissions and support operators
inspect connection logs. Reading connection logs does not authorize a new audit
trail for a permission-management operation. The probe is rejected as a complete
source-faithful repair; its artifacts remain unchanged.

For recognized positive permission-management clauses, detect unprovided concrete
create/delete/revoke operations, group subjects and database commitments in
normative statements and acceptance actions/outcomes/witnesses. Fixture setup in
GIVEN does not by itself create a supported product operation. Preserve actual
source-defined operations. This is a bounded heuristic, not general entailment.

When the only missing action is management and this source clause is recognized,
constrain the additional statement to a mechanical normative rendering of that
exact actor/action/object. The local model still authors rationale, classification
and test criteria. Independently check the fixed statement outside the decoder;
do not silently normalize a rejected free statement. Generic permission updates
can exercise management; unspecified detailed operations remain open decisions.

For sources that only mention existing logs, reject a new audit/access-control
log class absent from the source, as well as explicit new recording assertions.
External test captures and inspection of the actual source log remain allowed.
Record-source authority remains passage-bound. No dataset or provider changes.

Status: implementation and real-output verification in progress.

Integrated source-grounding-1.10 / repair-1.5. Full 365 tests passed, 24
third-party warnings; Ruff passed. Real probe 101910 completed in 33.0s on
three calls (adapter draft rejected for invented logging, base corrected row,
adapter witness patch). Actual content inspection confirms the selected
operation/group/database/audit expansions are absent; specific operations remain
unresolved. Original operator tests remain unchanged except the rejected witness.
Source stability true; bounded assistant review saved. No complete SRS claim.
