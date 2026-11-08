# ADR-0040: Bind supplemental permission tests to their missing source action

The real base-only campus run repeatedly returned a review action in WHEN while
claiming acknowledgement in THEN, even when explicitly asked to close the missing
acknowledgement test. It also copied rejected audit-log witnesses. Whole existing
requirements/tests in that small completion request encourage copying unrelated
or invalid criteria instead of exercising the missing action.

For a recognized permitted-action gap, derive its action only from the parsed
positive source permission. Provide the source, exact gap, and a compact canonical
ID/statement inventory; omit existing test bodies from this new-test request.
The server retains those tests independently. Bind the generated WHEN pattern to
the recognized source action and provide a fixed acknowledgement-specific remedy.
The independent permission oracle and full source/section validation still must
accept every replacement. No canned criterion is inserted after model failure.

Do not infer an action merely from a requested gap name, change normative behavior,
drop valid tests or introduce production logs/messages. Preserve bounded attempts,
actual model attribution and the trained-model-first policy. Record the narrow
repair-policy version. No provider/framework/training change is introduced.

Implemented as field-local-repair-1.2. Focused permission/repair tests: 18 passed;
integrated suite: 322 passed (24 third-party warnings); Ruff passed after fixing
import order and one long test string. Regressions reject the actual review-only
WHEN, bind only a permitted source action, and preserve the previous tests while
omitting their bodies from the new model request. A full adapter-first campus/VPN
evaluation is running in data/evaluations/20261028-075702-finetuned. Actual content
correctness remains unproven until its outputs are inspected.
