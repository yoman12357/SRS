# CyberSRS teacher demonstration

Open http://127.0.0.1:8011/ and select **Teacher demo - Campus access control**.
Use **Review specification** to view the generated document, **SDLC & delivery
workflow** for the ranked Agile choice, and **Export PDF** for the stored version.
If the app is stopped, double-click `start.cmd` in the project root.

The original project remains separate. This independent Desktop project reuses
the installed merged Qwen adapter and copied datasets; it does not retrain them.

## Demonstrate the workflow

1. Create a project and enter an informal cybersecurity/networking description.
2. Analyse it with local Ollama; answer or explicitly leave clarification decisions open.
3. Build the SRS. One coordinator runs each section specialist sequentially.
4. Review source evidence, requirements, architecture, threats/risks, linked use
   cases, verification and the evidence-based SDLC recommendation.
5. Export the exact stored JSON, Markdown or section-wise PDF. Human decisions
   belong to the exact document hash; generation does not approve the document.

The model authors structured decisions and acceptance criteria. The coordinator
validates JSON and composes source-linked views/process activities, which prevents
independent paraphrases from changing permissions or inventing product tasks.
Everything runs locally with SQLite, Ollama/Qwen, Chroma retrieval and React.

## Verified campus example

The real HTTP generation completed in 432 seconds. It produced five canonical
requirements, linked tests/use cases and an Agile workflow matching evolving
requirements and weekly feedback. The adapter was requested first; base Qwen
corrected rejected output, with actual model tags retained.

The report is a **prototype draft**. Some acceptance fixtures assume login, UI
behavior and audit fields not confirmed by the brief; those details require
review. Budgets, scheduling, concurrency and regulations remain unresolved.
No human approval or successful execution of the generated test plans is claimed.
See the exact-content review and exported files in
`data/demo-evaluations/20261028-172238/`.

Current checks: 428 backend tests pass; 9 frontend tests pass; production UI build
and Ruff pass. Automated checks establish selected invariants, not correctness
for every possible input.


The Research VPN case currently fails source validation during permission-management
acceptance generation. Use the verified Campus example for this demonstration;
general output reliability remains ongoing work. The latest campus PDF has31pages
with individual SDLC activity lists. The app's final local port is8011.
