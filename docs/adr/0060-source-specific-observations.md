# ADR-0060: Reject copied test templates and unconfirmed storage/session details

Both new examples completed under source policy 1.2, but final content inspection
found copied alternative object names in configuration acceptance tests. Generic
operation guidance listed policy/job/history options and the local model copied
the alternatives instead of choosing the source object. Other observations
introduced a policy registry/job history, all associated metadata, or session
persistence across operations without source confirmation.

Replace alternative examples with operation-specific guidance. Reject copied
template object placeholders, unsupported registry/history and persistence
choices, unspecified universal metadata promises, and display initiation without
an observed display result. These use the existing bounded authored-field repair
path, not hand-written replacement tests or relaxed validation. Preserve the
initial completed drafts as development evidence and rerun both descriptions
sequentially before replacing the Desktop deliverables.

The subsequent configuration run exposed a false rejection in the new display
check: a dashboard that displays data upon system initiation is an observed
display result, not merely an initiation claim. Evaluate the result clause after
separating its trigger/condition; retain the genuine initiation-only rejection.
Add the saved sentence and fronted-condition variants as explicit regressions.
