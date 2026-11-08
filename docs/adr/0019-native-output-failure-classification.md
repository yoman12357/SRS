# ADR-0019: Classify the observed native decoder failure as rejected output

2026-10-27. Two frozen-profile HTTP evaluations and a direct production retry
failed when the installed adapter emitted repeated JSON closures until its token
budget expired. Ollama returned HTTP 500 with the exact diagnostic "The model
produced output that does not match the expected peg-native format". The runtime
and installed model remained available. Private evidence is retained under
data/runtime-error-probe-1; no report or approval was fabricated.

Treat only this observed HTTP-500 diagnostic as a failed structured model response.
It consumes the existing bounded corrective retry budget, and may therefore invoke
the already disclosed same-Qwen base correction policy. Keep transport errors,
missing models and other server errors visible without model substitution. Never
render the raw error body; expose a fixed model_output_native_format_invalid code.
Successful correction still needs all existing Pydantic and semantic checks.

This fixes error classification, not the adapter weights or Ollama itself. It does
not establish better semantic output or successful full-workflow completion.

Profile 1.18's exact audit exposed a second model-output HTTP-500 diagnostic from
/api/generate: "prediction aborted, token repeat limit reached". Profile 1.19
classifies only that exact message as bounded output rejection as well. Other
server/transport failures remain visible without substitution. Cancellation is
checked immediately after HTTP completion before any corrective attempt.
