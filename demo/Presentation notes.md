# CyberSRS: short presentation notes

## What the project does

CyberSRS turns an informal cybersecurity or networking project description into
a structured SRS and an evidence-based SDLC recommendation. It runs locally.

## What to show

Open http://127.0.0.1:8011/ and select **Teacher demo - Campus access control**.
Show the original brief, then Review specification. Point out:

- Student/guest internet access and internal staff-network denial.
- Manual administrator isolation/restoration and the no-automation exclusion.
- Operator review/acknowledgement permissions and policy-change denial.
- Policy-change audit records and the source-stated 30-day duration.
- Linked use cases, verification plans and requirement traceability.
- Agile, justified by evolving requirements and weekly stakeholder feedback.

Open **Campus SRS and SDLC.pdf** in this folder for the exported document.
The PDF and JSON share the stored version's content hash.

## How it works

A local Qwen model analyses source evidence and asks clarification questions.
A deterministic coordinator calls section specialists in sequence through an
LLMProvider interface. Requirements retain model-authored acceptance criteria.
Downstream specialists choose source actors, flow variants, advisory hypotheses
and work groups; the coordinator composes linked views from canonical content.
SQLite stores checkpoints and immutable JSON versions. ReportLab renders the PDF.
Local Chroma retrieval supplies reference material with source metadata.

SDLC ranking uses versioned deterministic evidence rules. The local model explains
the winner; source-linked process compilation prevents invented product tasks
or delivery promises. Suitability scores are not accuracy probabilities.

## Model and limits

The installed merged Qwen adapter is requested first. Base Qwen can correct
rejected outputs, and actual model tags remain visible in AI drafting record.
The copied datasets/adapter are reused; no new training or improvement study is
claimed. Automated checks are not a guarantee of semantic correctness.

Present the result as a prototype draft: acceptance fixtures still need confirmation
of login/interface/audit details. Human approval belongs to an exact version hash.
The generated verification plans have not been executed against real networks.
