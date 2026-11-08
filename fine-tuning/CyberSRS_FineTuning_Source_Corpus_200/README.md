# CyberSRS Fine-Tuning Source Corpus — 200 Documents

This archive contains **exactly 200 source documents** for the Networking + Cybersecurity domain, organized into subdomain folders.

## Composition

- 100 documents from the existing CyberSRS source/RAG corpus (NIST, OWASP, RFC material)
- 100 additional selected IETF/RFC Editor documents covering identity, VPN/IPsec, TLS/PKI, DNS/DNSSEC, routing/BGP/RPKI, IPv6, HTTP/QUIC, email security, network management, and operational security/incident response
- 200 total source documents; root metadata files are not included in that count

## Important academic wording

These files are **source documents used to construct/ground a fine-tuning dataset**. A QLoRA/SFT model is normally trained on the structured examples (for example JSONL instruction/response records) generated or curated from these source documents — not simply by placing PDFs/TXT/MD files in a folder. Only state that the model was "fine-tuned directly on these documents" if your actual training pipeline tokenized these documents as training samples.

A precise project statement is:

> "We created the CyberSRS fine-tuning dataset from authoritative networking and cybersecurity requirement/specification sources, including NIST, OWASP, and IETF RFC documents."

## Root metadata

- `RESOURCE_LINKS.csv` — one row per source document, including official URL, subdomain, format, file hash, and provenance notes
- `RESOURCE_LINKS.md` — human-readable resource-link index
- `CORPUS_SUMMARY.json` — counts by subdomain and source organization

## Suggested next step

Extract requirement-bearing statements (especially NIST controls, OWASP ASVS/verification requirements, and RFC normative MUST/SHOULD/MUST NOT statements), then curate structured training examples with fields such as functionality/context, requirement, rationale/reasoning, acceptance criteria, source document, and source section. Keep final evaluation scenarios held out from training.

## Redistribution / attribution note

The bundle preserves the original source documents and lists their official source/reference URLs. Source-specific terms still apply. NIST publications may contain U.S. Government works and document-specific notices; OWASP materials have project-specific licenses; RFC documents are governed by IETF Trust Legal Provisions. Review those terms before redistributing beyond your academic/project use.
