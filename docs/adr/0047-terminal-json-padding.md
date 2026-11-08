# ADR-0047: Recover complete JSON followed only by closing-character padding

Actual VPN run d8ea136d-768a-42f1-a416-ecfa8f62b8e4 failed capacity completion.
Three base responses contained a complete schema-valid Requirement, then thousands
of repeated closing braces/backticks until Ollama's length limit. That complete
object invented a maximum of 25 sessions. The old length check prevented both
schema and semantic feedback, so retries repeated the same capacity error.

Permit one explicitly audited framing normalization: the response must start
with a complete JSON object, and every remaining non-whitespace character must
be a closing brace, closing bracket or backtick, with at least twelve padding
characters. Remove only that terminal padding. Never repair missing delimiters,
search inside prose/fences, accept a partial object, discard another object or
ignore meaningful trailing text. A length-limited response without qualifying
padding remains rejected, even if its visible JSON happens to be complete.

Parse the unchanged complete object through the ordinary schema, privacy restore
and full application semantic gate. The maximum-session claim must still fail.
Preserve the actual raw response, length reason, normalization event and model
call count. Successful provenance explicitly reports the removed padding; never
pretend Ollama stopped normally. This is framing repair, not source correction or
canonical content rewriting.

Also keep a rejected candidate's actual author distinct from a prior candidate
supplied by another model. Only a complete object actually returned by this
provider call can acquire this model's rejection authorship. Primary/base handoff
may retain an earlier complete rejected object with its original author.

Status: isolated implementation while the architecture probe is frozen.

Actual replay corrects the initial hypothesis: the latest base responses contain
additional objects after the first object, or an unmatched quote before repeated
closers. Across the frozen full evaluation, 11 length-limited responses yielded
ZERO qualifying closing-only suffixes (7 complete prefixes with other suffixes,
4 incomplete prefixes). The strict normalizer correctly rejects those wires.
Focused25/full386 software tests passed, but this does not address the actual
VPN failure. Do not promote this experiment as a verified fix. Next investigate
the bulk-section context inherited by a single-Requirement completion request.
