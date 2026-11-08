# ADR-0058: Recognize requested recording and independent permission operations

The latest PAM run failed in functional requirements because a positive
"should record" duty was not recognized as source-authorized recording.
Acceptance normalization removed requested logging, then field corrections
repeated the same false rejection. The source compiler also did not recognize
log, modify, suspend, require or control as independent predicates.

Recognize affirmative modal and active recording predicates, including should,
without treating reading existing logs, negation or a log-in action as permission
to create new event logs. Preserve requested recording during normalization.
Keep the existing rejection of unrequested logging and automatic responses.

Extend the bounded source predicate vocabulary and shared-object permission
lists. Normalize shared third-person purpose predicates without changing source
evidence. Add observable outcome checks and operation-specific test instructions
for these duties. Requirements remain source-compiled; criteria remain authored
by local Qwen and pass the same full validators. Existing bounded automatic
field correction stays in place; do not conceal exhausted budgets or genuine
semantic failures behind a success status.

Use the saved failed PAM output for offline regression/replay, plus the complete
backend suite. No new user project or generation is needed to prove this false
rejection is fixed. Live completion rate and timing require separately measured
model runs; no universal no-Retry claim is made.
