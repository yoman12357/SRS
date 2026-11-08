# Live document content review

The campus and VPN descriptions in scripts/live_check.py are authored development
regressions. They have been used to repair prompts and validators, so they are not
held-out quality evidence. A completed run or passing automated quality report is
not semantic acceptance. Record assistant inspection separately from human review.

For each completed document, record its exact version/hash, profile, actual model
authors, source snapshot and exported PDF. Check every obligation below against
canonical statements AND authored tests, citing the relevant requirement IDs.
The literal input register alone does not cover an omitted product obligation.

Campus:

- Students and guests can reach the internet; both are denied the staff network.
- Administrators can manually isolate a device and restore access. Exercise both.
- Security operators can review alerts and acknowledge them; exercise both.
- Operators cannot change access policies; exercise an attempted policy change.
- Record administrator policy changes, retaining audit records for 30 days.
  Do not expand the event scope or invent a minimum/maximum/deletion decision.
- Preserve 2,000 registered devices as planning inventory; concurrency stays open.
- No automatic firewall-rule changes or device isolation. Test both exclusions.
- Evolving requirements and weekly stakeholder feedback support Agile. The
  workflow must use actual iterations/feedback rather than freezing future changes.
- Budget, delivery schedule, response-time thresholds and mandatory frameworks
  remain unresolved. Do not turn open project decisions into runtime features.

VPN:

- Preserve the research-institute VPN goal and employee-specific MFA before access
  to approved research services. Do not broaden MFA to unnamed actors.
- Contractors can access only the support portal and cannot access research data.
  Exercise both permitted portal access and an attempted research-data access.
- Administrators manage permissions. Support operators inspect connection logs
  and cannot grant permissions. Do not infer other exclusive or denied roles.
- Retain connection logs for 14 days and remove them after expiry. Do not omit
  deletion or add an unqualified alternative retention bound.
- Preserve 250 registered users and 25 simultaneous sessions as distinct subjects.
- Exclude automatic firewall reconfiguration and active vulnerability scanning.
  Verify both, using simulated attempts and captured state/traffic in a test plan.
- Stable requirements and independent verification support V-Model. Independent
  does not imply mathematical formal verification. No continuous delivery is
  planned; this does not prove that iteration is impossible.
- Explicitly pair development/design stages with later technical and acceptance
  verification. Test plans must exist before implementation, with canonical
  requirement links, relevant roles, deliverables, entry/exit and human gates.
- Budget, schedule and protocol choices remain unresolved.

Across both documents, inspect source-linked logical architecture, relevant
threat/risk scenarios, linked actor stories, preserved acceptance criteria,
verification procedures, applicability matrix, glossary and traceability. Reject
unrequested product logs, technology/framework commitments and performance
thresholds. Proposed design/roles must remain proposed. Check the PDF cover,
contents, representative requirement/design/workflow pages and traceability for
clipping, missing text and usable pagination. Never post an assistant inspection
to the human-approval endpoint.

The separate scripts/heldout_compare.py fixes eval-001 and eval-006 before its
first run, uses exact original dataset bytes and identical adapter/base settings,
and disables correction by the other model. It must run after interactive work
is idle. Missing historical SDLC/threat/citation gold labels remain absent. Report
actual failures and limitations, without claiming statistical improvement or
expert-labelled SDLC accuracy from this two-description comparison.
