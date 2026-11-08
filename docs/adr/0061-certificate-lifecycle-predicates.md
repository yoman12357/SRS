# ADR-0061: Separate certificate approval and renewal obligations

The next requested test uses certificate request review, issuance approval,
renewal, revocation and status tracking. Source inspection showed approve and
renew were retained as text inside the review row instead of independent
testable predicates. Recognize those two source verbs without changing the input
or inventing an authority, protocol, algorithm or validity duration.

Keep explicit source actors and objects and ask local Qwen for observed approval
and renewal outcomes. Product certificate approval is distinct from human review
of this SRS; no document approval is recorded. Version the source/prompt policy
and verify existing regressions plus the exact new brief before running it.
