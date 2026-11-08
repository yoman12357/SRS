# ADR-0025: Exercise source actions and keep test captures distinct from product logs

2026-10-27. The frozen profile-1.21 campus run preserved the manual isolation and
restoration statement but added action audit logs in its acceptance outcomes.
Its architecture then propagated those logs beyond the requested policy-change
scope and added a minimum to the bare 30-day retention duration. Architecture
validation rejected that draft. The alert-view criterion also merely allowed
acknowledgement in its expected result without attempting acknowledgement.

The next bounded correction checks positive permission actions in the exercised
trigger, including explicit attempts stated in Given, rather than treating every
word in Then as an action that occurred. A request for data followed by its
returned view is an exercised inspection; an available acknowledgement button is
not an acknowledgement attempt. Initial isolated state alone does not test the
isolation action. Existing bounded model-authored test completion supplies gaps.

Acceptance validation also rejects assumed product logging and production-log
witnesses when the linked source specifies no logging. External test captures
remain permissible evidence; source-requested log views and recording remain
valid. This is a conservative observed-failure guard, not a universal entailment
proof or a ban on test instrumentation.

Known validator codes receive fixed plain-language corrective instructions on
retry and narrow repair. Arbitrary source or diagnostic text is never promoted
into the system instruction. Request budgeting includes the appended instructions;
the same schema, source and semantic checks still decide acceptance.

Profile 1.21 VPN also hid administrator management behind a denial of management
for operators, and inferred an exclusive administrator grant role. Coverage now
checks the affirmative named management role; an unsupported "only this role"
restriction is rejected against its linked source. These observed-case guards
do not establish general natural-language entailment.

The same run copied earlier requirements into its explicit noun-form automation
exclusion. Extend the source-bound prohibition vocabulary to this clear "out of
scope" form. Equivalent wording preserves the complete excluded action list.
Its one canonical row retains all model-authored tests; duplicate copies cannot
fill the passage. This bound is limited to an already fixed complete prohibition,
not a quota on other source obligations. Reconfiguration and scanning are distinct
actions and both require attempted-action/state verification.

Status: integrated in sequential-1.22. Full backend suite: 176 passed, with 24
third-party warnings. Fresh real outputs and their review remain required.
No human approval is inferred from these tests.
