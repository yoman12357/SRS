# CyberSRS Strict Cybersecurity + Networking SRS Corpus (50)

This corpus contains **50 SRS entries only**.

## Strict inclusion rule
Every entry:
1. Has an `AUTOSAR_SRS_*.pdf` filename (SRS).
2. Is directly related to networking, network management/monitoring, secure communication, cryptography, gateways, Ethernet/CAN/FlexRay/V2X, or network protocols.
3. Is NOT a generic hospital/library/e-commerce SRS.
4. Is NOT an AUTOSAR SWS/RS/PRS document.

## Important note
These are **50 versioned SRS documents**, built from 10 domain-relevant SRS titles across 5 AUTOSAR releases (R19-11 through R23-11). Therefore some titles repeat as different release revisions.

Because this execution environment cannot reliably download AUTOSAR PDF binaries, the ZIP includes:
- `SOURCES.csv`
- `.url` shortcuts for all 50 official source URLs
- `DOWNLOAD_ALL_WINDOWS.cmd`
- `download_all.ps1`

Run `DOWNLOAD_ALL_WINDOWS.cmd` after extraction to fetch the original PDFs.
