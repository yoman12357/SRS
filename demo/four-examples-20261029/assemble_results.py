"""Verify the final four live runs and publish their Desktop timing report."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pymupdf

from cybersrs.config import Settings
from cybersrs.repository import canonical_hash
from cybersrs.schemas import Document
from cybersrs.semantics import project_request_recast_as_runtime_behavior


def product_text(value: object) -> str:
    """Inspect authored product/delivery prose separately from retrieved library quotations."""
    if isinstance(value, dict):
        return " ".join(product_text(child) for key, child in value.items()
                        if key not in {
                            "sources", "evidence", "analysis", "unresolved_decisions", "open_issues"
                        })
    if isinstance(value, list):
        return " ".join(product_text(child) for child in value)
    return value if isinstance(value, str) else ""


def main() -> None:
    """Prove completion from the actual API, immutable content, run events and exported bytes."""
    root = Path(__file__).resolve().parent
    workspace = root.parents[1]
    desktop = workspace.parent / "CyberSRS - Four Examples"
    cases = json.loads((root / "cases.json").read_text(encoding="utf-8"))
    previous = json.loads((root / "final-results.json").read_text(encoding="utf-8"))
    release = json.loads((root / "release-results.json").read_text(encoding="utf-8"))
    results = [item for item in previous if item["case"] != "firewall"] + release
    assert {item["case"] for item in results} == {case["key"] for case in cases}
    snapshot = json.loads((root / "release-source-profile.json").read_text(encoding="utf-8"))
    assert all(hashlib.sha256((workspace / path).read_bytes()).hexdigest() == digest
               for path, digest in snapshot.items())
    settings = Settings()
    rows = []
    scans = {}
    patterns = {
        "invented_numeric_limit": r"\b\d+\s*(?:milliseconds?|seconds?|minutes?|hours?|days?|"
                                  r"weeks?|months?|attempts?|MB|GB|Mbps|Gbps)\b",
        "wifi_standard_or_protocol": r"\b(?:802\.11\w*|802\.1X|WPA[23]?|WEP|RADIUS|EAP-TLS|PEAP|"
                                     r"TACACS|SAML|OpenID|OAuth)\b",
        "vlan_or_ip_or_port": r"\bVLAN\s+\d+|\b(?:\d{1,3}\.){3}\d{1,3}\b|\bport\s+\d+",
        "vendor_or_endpoint_product": r"\b(?:Cisco|Fortinet|Palo Alto|Proofpoint|Mimecast|"
                                      r"Sophos|ClamAV|Kaspersky|Symantec|CrowdStrike|"
                                      r"SentinelOne|Wazuh|osquery|Sysmon)\b",
        "os_requirement": r"\b(?:Windows|Linux|macOS)\b",
        "specific_ml_model": r"\b(?:BERT|Random Forest|SVM|XGBoost)\b",
    }
    with httpx.Client(base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1",
                      timeout=30) as client:
        assert client.get("/health").json()["status"] == "ready"
        for case in cases:
            result = next(item for item in results if item["case"] == case["key"])
            assert result["status"] == "completed" and result["source_unchanged"]
            run = client.get("/runs/" + result["generation"]["run_id"]).json()
            assert run["status"] == "completed" and not run["error"]
            completed = [event for event in run["events"]
                         if event.get("state") == "completed" and event.get("agent") != "document"]
            assert len(completed) == 14 and not any(event.get("reused") for event in completed)
            assert result["manual_retries"] == 0
            assert all(event.get("elapsed_seconds", 0) <= settings.section_timeout_seconds
                       for event in completed)
            base = f"/projects/{result['project_id']}/versions/{result['version_id']}"
            response = client.get(base)
            response.raise_for_status()
            version = response.json()
            assert version["content_hash"] == result["content_hash"]
            assert canonical_hash(version["content"]) == version["content_hash"]
            assert version["quality"]["status"] != "invalid"
            doc = Document.model_validate(version["content"])
            assert doc.prompt_version in {"sequential-1.29", "sequential-1.30"}
            assert doc.original_description == case["description"]
            assert not client.get(base + "/reviews").json()
            source = {item.id: item.quote for item in doc.evidence}
            for category in ("functional", "nonfunctional", "security", "data", "network"):
                for requirement in getattr(doc, category).requirements:
                    assert not any(project_request_recast_as_runtime_behavior(
                        source[eid], requirement.statement) for eid in requirement.evidence_ids)
            output = root / (case["key"] + "-" + result["label"])
            pdf_path = desktop / (case["filename"] + ".pdf")
            assert pdf_path.read_bytes() == (output / "SRS.pdf").read_bytes()
            with pymupdf.open(pdf_path) as pdf:
                text = " ".join(" ".join(page.get_text().split()) for page in pdf)
                assert "IEEE 830-1998" in text and "DRAFT" in text
                assert version["content_hash"] in text
                for section in version["presentation"]["sections"]:
                    for requirement in section["requirements"]:
                        assert " ".join(requirement["statement"].split()) in text
            prose = product_text({key: version["content"][key] for key in (
                "introduction", "functional", "nonfunctional", "security", "data", "network",
                "architecture", "verification", "scenarios", "sdlc", "threats", "risks", "glossary"
            )})
            scan = {name: re.findall(pattern, prose, re.I) for name, pattern in patterns.items()}
            scans[case["key"]] = scan
            rows.append({
                "case": case["key"], "generation_seconds": result["generation"]["total_seconds"],
                "analysis_seconds": result["analysis"]["total_seconds"],
                "wall_seconds_including_export": result["total_wall_seconds"],
                "maximum_section_seconds": result["generation"]["maximum_section_seconds"],
                "sections_completed": len(completed), "reused_sections": 0, "manual_retries": 0,
                "automatic_model_attempts": sum(event.get("attempts", 0) for event in completed),
                "pdf_pages": result["pdf_pages"], "pdf_sha256": hashlib.sha256(
                    pdf_path.read_bytes()).hexdigest(),
                "canonical_hash": version["content_hash"], "quality": version["quality"]["status"],
                "project_id": result["project_id"], "version_id": result["version_id"],
                "run_id": run["id"], "pdf": str(pdf_path),
                "prompt_version": doc.prompt_version, "attempt_label": result["label"],
            })
    (root / "constraint-scan.json").write_text(json.dumps(scans, indent=2), encoding="utf-8")
    (root / "verified-results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    assert not any(matches for scan in scans.values() for matches in scan.values()), scans
    lines = [
        "# CyberSRS — four-example generation results", "",
        "Checked on " + datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %B %Y, %I:%M %p IST"),
        "", "The latest fresh run of each example completed all 14 sections without a "
        "manual Retry, "
        "checkpoint reuse or section edits. Automatic model corrections remained enabled. "
        "The section limit stayed at 60 seconds. These are real local Ollama runs, not fixtures.",
        "", "| Example | Generation | Analysis | PDF pages | Manual Retry |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for case, row in zip(cases, rows, strict=True):
        seconds = round(row["generation_seconds"])
        lines.append(f"| {case['name']} | {seconds // 60}:{seconds % 60:02d} | "
                     f"{row['analysis_seconds']:.1f} s | {row['pdf_pages']} | 0 |")
    lines += [
        "", "Generation timings exclude analysis and PDF export. Exact values and run/version "
        "IDs are in verified-results.json in the evidence folder.", "",
        f"Slowest final generation: {max(row['generation_seconds'] for row in rows):.3f} seconds. "
        f"Slowest section: {max(row['maximum_section_seconds'] for row in rows):.3f} seconds.",
        "", "## What was found and fixed", "",
        "The initial pass completed Wi-Fi and email, but endpoint and firewall failed. "
        "The endpoint purpose was incorrectly required to include a management verb because "
        "it referred to managed endpoints; system-event collection also failed a narrow "
        "monitoring-purpose check. Firewall drafting moved actions between source passages. "
        "A later completed firewall draft also recast the request to design a system as a "
        "runtime feature and was held back for correction.", "",
        "The fixes preserve genuine management/monitoring duties, strengthen source-ID "
        "binding, reject project-request verbs as runtime functions, and allow a bounded "
        "model-authored repair of only rejected source groups. Every candidate still passes "
        "the full validator. Valid neighboring groups remain frozen. All earlier attempts "
        "remain in the evidence folder; they are not counted as first-pass successes.",
        "", "## Checks and limits", "",
        "516 backend tests passed (24 existing dependency warnings); Ruff passed. "
        "The frontend was unchanged. Live API/schema/hash checks pass for all four final "
        "versions. Every canonical requirement appears in the exported IEEE PDF. Source "
        "hashes stayed unchanged during each selected run, and no human approval was recorded. "
        "Wi-Fi, email and endpoint ran sequential-1.29; firewall then ran sequential-1.30 "
        "after a raw non-normative repair exposed one more failure. The current API "
        "revalidated all four selected versions without rewriting their content.",
        "", "A targeted scan of authored product/delivery prose found no concrete values "
        "for the excluded thresholds, durations, sizes, VLAN/IP/port choices, named Wi-Fi "
        "protocols, endpoint products/OS requirements or specific ML models. Retrieved library "
        "quotations and explicitly unresolved questions were excluded from that scan because "
        "references and open questions are not confirmed product decisions. For example, "
        "the Wi-Fi draft mentions 802.1X as an example in an unanswered protocol question; "
        "it does not select that protocol as a requirement. "
        "This is a bounded check, not a proof of complete semantic correctness.",
        "", "All PDFs are drafts. Some compound acceptance criteria and broad quality "
        "claims still need stakeholder review. SDLC selection has the previously discussed "
        "limitations and was not redesigned in this task. Four successful final runs do not "
        "establish that every future brief will avoid Retry or that these times are a universal "
        "worst-case bound.", "", "Evidence folder: " + str(root),
    ]
    text = "\n".join(lines) + "\n"
    (root / "Generation results.md").write_text(text, encoding="utf-8")
    (desktop / "Generation results.md").write_text(text, encoding="utf-8")
    (desktop / "verified-results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
