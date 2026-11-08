# Scope

Implement the PRD as a local FastAPI/Python modular monolith, React/TypeScript/Vite
client, SQLite, ChromaDB, local Ollama/Qwen3-4B and nomic-embed-text. Use standard
Python orchestration; no agent framework or new provider. PDF uses ReportLab,
already approved in the source project. SQLite uses the Python standard library.

Reuse adapter and historical datasets without retraining or modifying labels.
Retain held-out evaluation splits. An installed merged adapter model is reused
through its Ollama tag; do not attach the QLoRA delta to a separately quantized
base model. All application inference and embeddings stay on loopback.

Generated documents describe defensive systems. The platform does not execute
scans/exploits, change infrastructure, deploy code or access cloud models. User
content stays in local storage and is never written to debug logs or training data.
Retrieved/reference text is untrusted evidence, never executable instructions.
