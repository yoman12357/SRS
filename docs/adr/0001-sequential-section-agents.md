# ADR-0001: Fresh sequential section-agent architecture

Accepted by explicit user request on 2026-10-27. Create a new Desktop project;
reuse local datasets, adapter and useful UI assets. Replace grouped generation
with one orchestrator and one Ollama-backed specialist for each SRS section.
Agents run sequentially, share validated structured context, and never execute
tools beyond provider inference and read-only local retrieval. No new framework.

Preserve the approved source stack and local/security boundaries. Use standard
sqlite3 instead of the source ORM. Store canonical section JSON before rendering
PDF; human approval and validation remain distinct. The cost is additional local
inference latency; report measured runtime rather than promising eight minutes.

Historical documents are preserved as reference, not copied implementation or
evidence that this new app is finished. The professor's financial examples are
adapted to networking/cybersecurity, consistent with the user's project scope.
