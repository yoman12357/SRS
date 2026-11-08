# Project Resources

The runtime ingests the documents in `knowledge/`. The starter corpus ZIP and
its historical README are retained for reference. Original publisher links are
recorded in the knowledge and training corpus manifests.

- NIST publications retain their original attribution and document notices.
  [NIST publication information](https://www.nist.gov/itl/publications-0/nist-special-publication-800-series-general-information)
- OWASP Cheat Sheets and ASVS source material are provided under CC BY-SA 4.0.
  [Cheat Sheet Series](https://owasp.org/projects/cheat-sheet-series), [ASVS](https://owasp.org/projects/asvs)
- RFC text retains its original notices. [IETF Trust Legal Provisions](https://trustee.ietf.org/documents/trust-legal-provisions/)
- AUTOSAR PDF downloads are kept local. The corpus includes the official links
  and its original download script for obtaining those optional training sources.

The public checkout omits private inference dumps and the original academic
brief. The adopted project requirements are recorded in
[`PROBLEM_STATEMENT_ALIGNMENT.md`](PROBLEM_STATEMENT_ALIGNMENT.md).

The raw adapter is an optional release asset. To include its bytes in a local
asset audit, download it to
`fine-tuning/CyberSRS_Qwen3_4B_LoRA_Adapter/adapter_model.safetensors`.
[Raw QLoRA adapter](https://github.com/yoman12357/SRS/releases/download/v0.1.0/adapter_model.safetensors)
