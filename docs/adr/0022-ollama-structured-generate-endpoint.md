# ADR-0022: Use Ollama's structured generate endpoint for single-turn specialists

2026-10-27. A controlled diagnostic used the same system/data/schema/options and
installed models after all application inference was idle. Adapter /api/generate
returned schema-valid JSON in 9.891 seconds; /api/chat returned the observed native
format HTTP-500 error after 104.906 seconds. Base /api/generate also returned
schema-valid JSON in 9.235 seconds. Neither generate response passed the prohibition
test oracle: protocol reliability and semantic correctness are separate results.
Exact private requests/responses are in data/native-protocol-probe-1/report.json.

Each provider request already consists of one system instruction and one data
message, with no ongoing chat history. Use the documented /api/generate system,
prompt and format fields for these requests, and parse its response field. Keep
the same installed Qwen models, schema constraints, options, correction limits,
source validation and actual-author provenance. This changes an endpoint inside
OllamaProvider, not the provider-independent interface or approved LLM provider.

Official endpoint contract: https://docs.ollama.com/api/generate

Record exact generate payloads/responses in the new local audit. Unit tests must
cover this wire contract. Actual complete SRS/SDLC output still requires evaluation
and semantic/PDF review; a schema-valid protocol probe is not an accepted document.
