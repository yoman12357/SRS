# ADR-0062: Constrain API observation repairs instead of repeating rejected guesses

The API access-management run failed after 41 seconds, despite a 120-second
section budget. The corrective model repeated an invented numeric response code
and account lockout. Its feedback was too generic. Detection guidance was omitted
when the parent paragraph also mentioned alerts, even though detection was an
independent source operation. The enforce-result matcher also missed the valid
active wording "denies access".

Accept active/passive access-decision inflections. Always scope each detection
test to recognition of its named condition, and distinguish it from response
actions. Give enforce/authenticate operations their own source-specific guidance.
For rejected free-text fields preserve the original short-field bounds and
constrain native repair output to no digits when the source has no numeric
values. Enforce/detect result repairs must include an observable decision or
recognition predicate; full semantic validation still rejects unsupported
responses and fields. These constraints guide authored text rather than replacing
criteria with canned defaults or weakening failed-document checks.

Use the existing configurable bounded field-repair limit, three for this demo
deployment, under the same section deadline. No infinite retries, fabricated
success, omitted requirements, changed model provider or automatic human approval.
Keep the user's successful existing retry and failed history intact. Verify fresh
API-brief runs, both render formats and regression tests before reporting readiness.
