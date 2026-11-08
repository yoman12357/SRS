# CyberSRS QLoRA Adapter Deployment

## Runtime Contract

CyberSRS continues to use the provider-independent `LLMProvider` boundary. General
chat uses `CYBERSRS_BASE_MODEL_NAME`; SRS analysis, clarification, generation, and
editing use `CYBERSRS_FINETUNED_MODEL_NAME` only when
`CYBERSRS_MODEL_VARIANT=finetuned`. RAG retrieval is independent and continues to
supply selected local sources to the active SRS model.

The fine-tuned Ollama tag is a GGUF made by merging the QLoRA delta into the exact
full-precision training base and quantizing the merged model. Do not attach this
bitsandbytes-trained Qwen adapter directly to a separately quantized base model:
that combination produced corrupt structured output during local validation.

## Local Artefacts

The local adapter source is expected under:

```text
fine-tuning/CyberSRS_Qwen3_4B_LoRA_Adapter/
  adapter_config.json
  adapter_model.safetensors
```

The adapter directory and generated model weights are local-only and ignored by
Git. The tracked Ollama definition is:

```text
models/cybersrs-qwen3-4b-ft_gguf/FineTunedModelfile
```

Its `FROM` path points to the locally generated merged and quantized GGUF. The
merge must use the exact base revision recorded by the adapter configuration;
substituting another Qwen release is not valid.

## Registration

After producing the merged GGUF beside the Modelfile, register or refresh the
dedicated Ollama tag from the repository root:

```powershell
ollama create cybersrs-qwen3-4b-ft `
  -f .\models\cybersrs-qwen3-4b-ft_gguf\FineTunedModelfile
ollama list
```

Then configure `.env` and restart the backend:

```text
CYBERSRS_LLM_PROVIDER=ollama
CYBERSRS_MODEL_VARIANT=finetuned
CYBERSRS_BASE_MODEL_NAME=qwen3:4b-instruct-2507-q4_K_M
CYBERSRS_FINETUNED_MODEL_NAME=cybersrs-qwen3-4b-ft
CYBERSRS_RAG_ENABLED=true
```

Ollama may report the registered model as `cybersrs-qwen3-4b-ft:latest`; the
readiness preflight treats an omitted tag as `latest`. It does not silently use
the base model when the configured fine-tuned tag is absent.

## Verification and Rollback

Before treating the adapter as production-ready:

1. Confirm the configured tag is present and the backend readiness check is
   `ready`.
2. Run the base and fine-tuned variants against the same five cybersecurity and
   networking QA scenarios.
3. Compare schema validity, requirement correctness, measurable verification,
   citation precision/coverage, latency, and unsafe-output checks.
4. Confirm stored provenance identifies the fine-tuned model and RAG retrieval
   separately.

Connection success does not prove quality. If the adapter produces more invalid
or incomplete structured output than the base model, set
`CYBERSRS_MODEL_VARIANT=base`, restart the backend, and retain the evaluation
results for the next training-data revision.
