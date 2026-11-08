# ADR-0027: Distinguish sign-in from event logging and represent real trust domains

2026-10-27. Frozen profile 1.24 failed campus architecture because the event-log
guard matched a security operator who "logs into" a dashboard. Its interaction
draft also drew network trust boundaries from the policy engine to itself. The
first architecture stage named only internal modules, leaving no distinct actor
or network-zone endpoints for the constrained second stage.

Use a shared event-logging predicate that distinguishes logical descriptions,
sign-in actions and auditor roles from actual log/audit records. A sign-in source
does not authorize unrelated event logging. Actual application logs and logged
JSON events still require the same source support.

The component inventory must include source-backed external actors, network zones
and resources needed for the interactions. These are logical architecture nodes,
not separate deployments or new microservices. A trust boundary needs distinct
untrusted and trusted domains; its inventory must have room for both. This is a
structural minimum for the boundary representation, not a requirement-count quota.

The VPN case also falsely rejected a support operator opening the log dashboard
and receiving its data because the trigger did not say "request" or "inspect".
Recognize dashboard access/navigation with actual returned or displayed data.
An available inspection button is not the data. Keep the named actor in the test;
another role's access does not prove support-operator access. Administrator/admin
are equivalent role spellings. Write/state-changing actions still need their own
exercised triggers.

Status: integrated in sequential-1.25. Main backend: 213 tests pass with 24
third-party warnings; Ruff lint/format pass. Real document review remains required.
No semantic acceptance or human approval follows from these regressions alone.
