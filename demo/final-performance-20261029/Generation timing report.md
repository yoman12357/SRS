# Generation timing report - 2026-10-29

Two real local runs on the configured Qwen adapter-first profile. Each generated all 14 sections without reusing section checkpoints. Timing starts at the generation request and excludes prior analysis and the separately measured PDF export.

| Case | Generation | Slowest section | PDF export | Result |
| --- | ---: | ---: | ---: | --- |
| University VPN | 96.768 s | 22.027 s | 0.797 s | Complete draft |
| Campus access control | 84.166 s | 27.482 s | 1.000 s | Complete draft |

| Section | University VPN | Campus access control |
| --- | ---: | ---: |
| introduction | 2.009 s | 2.017 s |
| functional | 15.924 s | 26.606 s |
| nonfunctional | 18.912 s | 0.021 s |
| security | 11.189 s | 27.482 s |
| data | 0.020 s | 0.022 s |
| network | 0.019 s | 0.016 s |
| compliance | 11.673 s | 7.777 s |
| architecture | 22.027 s | 3.552 s |
| threats | 1.888 s | 2.171 s |
| risks | 1.652 s | 1.814 s |
| scenarios | 1.374 s | 2.066 s |
| verification | 5.205 s | 5.155 s |
| glossary | 1.418 s | 1.708 s |
| sdlc | 3.079 s | 3.395 s |

The zero/near-zero category times are deterministic indexes of existing canonical requirements, not invented model calls. The adapter remains the primary author; actual base-model corrections are recorded in run/section provenance. No human approvals were recorded.

Verification: 439 backend tests pass (24 existing third-party warnings); Ruff passes. All 12 frontend tests and the TypeScript/Vite production build pass. Both PDFs were sampled visually; the university PDF has 26 pages and the campus PDF 31 pages. Stored JSON/source descriptions match exactly, all 14 sections are complete, no checkpoint reuse occurred, and export/quality routes use the stored immutable versions.

The drafts pass selected automated checks (VPN 24/24; campus 26/26). Semantic correctness and complete clause-level acceptance coverage still require human review. For example, the VPN administrative-action group preserves all stated actions but its generated acceptance criterion does not separately exercise every action. No formal correctness, human approval, executed target-system tests, or adapter-improvement claim is made.

Reproduce observation/export for an existing run with `scripts/measure_run.py --base-url <loopback-app-url> --run-id <id> --output <folder>`. An observation timeout never restarts the model or declares the run stopped.

## University VPN
Run: `b58f9cdf-a2ef-4b66-9f99-56b534c3f5cf`
Version: `a2a586a0-cdb8-4ad6-a076-a3a976302b53`
Started: `2026-10-29T03:17:35.940420+00:00`
Finished: `2026-10-29T03:19:12.708049+00:00`
Artifacts: `university-vpn/run.json`, `timing.json`, `srs.json`, `SRS.pdf`

## Campus access control
Run: `0eae7064-0601-48e0-ac95-8ef659710c2f`
Version: `a58cf83f-b305-4d98-9109-5c438b8a94cb`
Started: `2026-10-29T03:19:14.220749+00:00`
Finished: `2026-10-29T03:20:38.386662+00:00`
Artifacts: `campus-access/run.json`, `timing.json`, `srs.json`, `SRS.pdf`
