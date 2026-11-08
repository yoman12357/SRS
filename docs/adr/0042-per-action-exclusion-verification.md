# ADR-0042: Complete excluded-action tests one source action at a time

The trained-first run in data/evaluations/20261028-075702-finetuned repeatedly
returned an automatic device-isolation attempt in GIVEN while WHEN merely said
"the action is executed". It did not independently attempt firewall modification.
The aggregate prohibition gap correctly rejected it, but the single request to
verify all missing actions did not converge.

Keep the public aggregate exclusion oracle and its mandatory final source gate.
Internally enumerate the source's actual uncovered actions and ask for one missing
action per bounded completion call. A response that correctly covers several
actions may close several gaps; retain valid existing tests and do not force
duplicate criteria. Bind WHEN to the target source action and keep the attempted
action explicit in WHEN, with observable unchanged/absent outcomes and external
state evidence. No new excluded action may come from a fabricated gap name.

Preserve action mode: an explicit active-scanning exclusion can be exercised as
an active scan; it is not necessary to invent an automatic-only scope for it
merely because another clause excludes automatic firewall changes. Recognize
scan-absence packet/traffic observations separately from configuration changes.
All proposed tests remain simulated/authorized plans; the platform executes none.

No canonical statement, source fact, model/provider, retry cap or training label
changes. Record the narrow repair-policy version and run independent parser,
source and final aggregate checks.

Implemented as field-local-repair-1.3 / source-grounding-1.7. Staged and main
suites passed 342 tests (24 third-party warnings); Ruff passed. One full staged
run exposed a legitimate network-trace synonym; corrected it while retaining the
rejection of configuration-only scan evidence. The real source-scoped probe in
data/source-test-probes/20261028-084057 repaired the actual rejected campus row in
two trained-adapter calls (11.2 seconds), with no base correction. Inspection found
explicit isolation/modification attempts in WHEN, unchanged outcomes and before/
after evidence, and unchanged normative metadata. Source stability is true. This
does not establish a complete SRS or execute a forbidden action.
