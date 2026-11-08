# ADR-0005: Adapter-first inference with transparent base-Qwen correction

Real runs show that the historical adapter does not reliably obey the new runtime
contracts. It has omitted manual actors, invented references and restated
requirements as test evidence. The base Qwen variant can correct some of these
failures. Neither variant is trusted without the same validation.

The production provider first asks the configured (normally fine-tuned) local Qwen
model. After bounded structured/semantic validation failure, it may ask the local
base checkpoint of the same approved Qwen model for correction. This remains
Ollama behind LLMProvider; no new model family, cloud provider, mock or template
report is introduced. Missing models, transport failures, cancellation and expired
budgets do not trigger a hidden substitution.

This policy is configurable with CYBERSRS_BASE_REPAIR_ENABLED. Events and saved
documents record requested and actual output model tags and fallback reasons.
Pure adapter/base evaluation disables this policy unless --repair is explicit.
No adapter-improvement claim is justified by corrected mixed-variant output.
