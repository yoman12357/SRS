# ADR-0013: Ground generation in trusted field definitions

The provider supplied JSON Schema to Ollama's decoder but did not show its field
definitions to the model. [Ollama recommends also including the schema in the
prompt](https://docs.ollama.com/capabilities/structured-outputs). Include the
trusted Pydantic schema in the system instruction and count its bytes in the
context budget. Keep the stricter source-specific schema in the decoder format.

Do not promote source-derived quote enums or role labels into the system message.
Those untrusted values stay in the user data and decoder constraints. Parsed
schema and source/relationship/observable-outcome validation still apply; schema
grounding alone is not evidence of semantic correctness.

The installed base is verified as Qwen3-4B-Instruct-2507; the merged adapter and
base use distinct GGUF blobs. Their local metadata/digests are recorded under data.
[Qwen's general sampling guidance](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
uses temperature 0.7, top-p 0.8 and top-k 20. This structured-output implementation
uses temperature zero, consistent with Ollama's guidance for deterministic JSON.
No improvement claim follows from either setting without matched evaluation.
