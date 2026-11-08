"""Deterministic section-wise Markdown and PDF rendering from canonical JSON."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from .schemas import SECTION_SCHEMAS, Document

LABELS = {
    "compliance": "Compliance and policy applicability matrix",
    "nonfunctional": "Non-functional requirements",
    "functional": "Functional requirements",
    "security": "Security, privacy and compliance",
    "network": "Network and interfaces",
    "data": "Data requirements",
    "scenarios": "User stories and use cases",
    "verification": "Verification and acceptance",
    "sdlc": "SDLC recommendation and workflow",
    "verification_pairs": "V-Model development and verification pairing",
    "test_plan_deliverable": "Test plan created in the development phase",
}


def document_status(version: dict, reviews: list[dict]) -> str:
    """Human approval belongs only to an exact hash and the latest decision."""
    if version["quality"]["status"] == "invalid":
        return "INVALID DRAFT — corrections required"
    if (
        reviews
        and reviews[-1]["decision"] == "approve"
        and reviews[-1].get("content_hash") == version["content_hash"]
    ):
        return "HUMAN-APPROVED BASELINE"
    return "DRAFT — human review required"


def _label(key: str) -> str:
    return LABELS.get(key, key.replace("_", " ").capitalize())


def _markdown_literal(value: object) -> str:
    text = str(value).replace("\\", "\\\\")
    text = re.sub(r"([`*_\[\]<>])", r"\\\1", text)
    return re.sub(r"(?m)^(\s*)([#>+-]|[0-9]+[.)])", r"\1\\\2", text)


def _markdown_value(value, level: int = 3) -> list[str]:
    lines: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            lines += ["", f"{'#' * min(level, 6)} {_label(key)}", ""]
            lines += _markdown_value(nested, level + 1)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                lines += _markdown_value(item, level)
                lines += ["", "---", ""]
            else:
                lines.append(f"- {_markdown_literal(item)}")
        if not value:
            lines.append("None recorded.")
    else:
        lines.append(_markdown_literal(value))
    return lines


def render_markdown(version: dict, reviews: list[dict], *, detail: str = "standard") -> str:
    """Render the IEEE reader report or the complete supporting representation."""
    if detail == "full":
        return _render_full_markdown(version, reviews)
    from .ieee_exports import render_srs_markdown

    return render_srs_markdown(version, document_status(version, reviews))


def _render_full_markdown(version: dict, reviews: list[dict]) -> str:
    """Render every canonical section, original evidence and traceability losslessly."""
    document = Document.model_validate(version["content"])
    payload = document.model_dump()
    lines = [
        f"# {_markdown_literal(document.title)}",
        "",
        document_status(version, reviews),
        "",
        f"Version {version['sequence']} | {version['created_at']}",
        "",
        f"Content SHA-256: {version['content_hash']}",
        "",
        "AI-generated advisory document. A qualified person must review its correctness.",
        "Automated checks are heuristic; SDLC scores are suitability points, not probabilities.",
        "",
        "## Original project description",
        "",
        _markdown_literal(document.original_description),
    ]
    for index, section in enumerate(SECTION_SCHEMAS, start=1):
        lines += ["", f"## {index}. {_label(section)}"]
        lines += _markdown_value(payload[section])
    for label, data in [
        (
            "SDLC decision evidence",
            {
                "policy": document.sdlc_policy_version,
                "generation_profile": document.sdlc_prompt_version,
                "factors": payload["sdlc_factors"],
                "ranked_candidates": payload["sdlc_candidates"],
            },
        ),
        ("Original evidence", payload["evidence"]),
        ("Source references", payload["sources"]),
        ("Quality and traceability", version["quality"]),
        ("Human review history", reviews),
        (
            "Generation provenance",
            {
                "requested_model": document.requested_model_name,
                "actual_models_used": document.models_used,
                "section_models": document.section_models,
                "prompt_version": document.prompt_version,
            },
        ),
    ]:
        lines += ["", f"## {label}"] + _markdown_value(data)
    return "\n".join(lines) + "\n"


class SRSDocTemplate(BaseDocTemplate):
    """Add navigable section bookmarks and a generated table of contents."""

    def afterFlowable(self, flowable) -> None:
        """Collect only section headings for the second-pass contents render."""
        if isinstance(flowable, Paragraph) and flowable.style.name == "SectionHeading":
            key = f"section-{self.seq.nextf('section')}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, level=0)
            self.notify("TOCEntry", (0, flowable.getPlainText(), self.page, key))


def render_pdf(version: dict, reviews: list[dict], *, detail: str = "standard") -> bytes:
    """Render the IEEE reader PDF or its exhaustive supporting report."""
    if detail == "full":
        return _render_full_pdf(version, reviews)
    from .ieee_exports import render_srs_pdf

    return render_srs_pdf(version, document_status(version, reviews))


def _render_full_pdf(version: dict, reviews: list[dict]) -> bytes:
    """Create a paginated professional PDF from exactly the validated stored JSON."""
    document = Document.model_validate(version["content"])
    font_root = Path(reportlab.__file__).parent / "fonts"
    for name, file in [("SRS", "Vera.ttf"), ("SRS-Bold", "VeraBd.ttf")]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(font_root / file)))
    pdfmetrics.registerFontFamily("SRS", normal="SRS", bold="SRS-Bold", italic="SRS")
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "BodySRS", fontName="SRS", fontSize=9, leading=13, spaceAfter=6, wordWrap="CJK"
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionHeading",
            fontName="SRS-Bold",
            fontSize=17,
            leading=22,
            spaceAfter=14,
            keepWithNext=True,
            textColor=colors.HexColor("#12635c"),
        )
    )
    styles.add(
        ParagraphStyle(
            "SubheadingSRS",
            fontName="SRS-Bold",
            fontSize=10,
            leading=15,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverSRS",
            fontName="SRS-Bold",
            fontSize=28,
            leading=36,
            alignment=TA_CENTER,
            spaceAfter=24,
        )
    )
    story = []
    styles.add(ParagraphStyle("ContentsHeading", parent=styles["SectionHeading"]))
    styles.add(
        ParagraphStyle(
            "ListSRS",
            parent=styles["BodySRS"],
            leftIndent=13,
            bulletIndent=0,
            spaceAfter=5,
        )
    )

    def para(text: str, style: str = "BodySRS"):
        # Escape all user/model content before ReportLab's XML-like paragraph parser.
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles[style])

    def value_rows(value, depth: int = 0):
        if isinstance(value, dict):
            title = value.get("title")
            identifier = value.get("id")
            if title:
                story.append(
                    para(f"{identifier + ' - ' if identifier else ''}{title}", "SubheadingSRS")
                )
            for key, nested in value.items():
                if nested in ([], {}, "", None) or (title and key in {"id", "title"}):
                    continue
                if isinstance(nested, (str, int, float, bool)):
                    label_text = escape(_label(key))
                    content = escape(str(nested)).replace("\n", "<br/>")
                    story.append(Paragraph(f"<b>{label_text}:</b> {content}", styles["BodySRS"]))
                elif isinstance(nested, list) and all(
                    not isinstance(item, (dict, list)) for item in nested
                ):
                    label_text = escape(_label(key))
                    if key in {
                        "activities",
                        "deliverables",
                        "entry_criteria",
                        "exit_criteria",
                        "security_checks",
                        "preconditions",
                        "steps",
                        "alternate_flows",
                        "procedure",
                        "tradeoffs",
                        "assumptions",
                    }:
                        story.append(para(_label(key), "SubheadingSRS"))
                        for index, item in enumerate(nested, 1):
                            story.append(
                                Paragraph(
                                    escape(str(item)).replace("\n", "<br/>"),
                                    styles["ListSRS"],
                                    bulletText=f"{index}.",
                                )
                            )
                        continue
                    content = "; ".join(escape(str(item)) for item in nested)
                    story.append(Paragraph(f"<b>{label_text}:</b> {content}", styles["BodySRS"]))
                else:
                    story.append(para(_label(key), "SubheadingSRS"))
                    value_rows(nested, depth + 1)
        elif isinstance(value, list):
            if not value:
                story.append(para("None recorded."))
            for item in value:
                if isinstance(item, dict):
                    value_rows(item, depth)
                    story.append(Spacer(1, 1.5 * mm))
                else:
                    story.append(para(f"• {item}"))
        else:
            story.append(para(str(value)))

    status = document_status(version, reviews)
    story += [
        Spacer(1, 35 * mm),
        para("CYBERSRS", "SubheadingSRS"),
        para(document.title, "CoverSRS"),
        para("Software Requirements Specification"),
        para(status),
        para(f"Version {version['sequence']} • {version['created_at']}"),
        Spacer(1, 12 * mm),
        para("AI-generated advisory document. Review by a qualified professional is required."),
        para(
            "Automated checks do not prove completeness or semantic correctness. "
            "SDLC suitability scores are rule-based points, not probabilities."
        ),
        para(f"Content SHA-256: {version['content_hash']}"),
        PageBreak(),
    ]
    story.append(para("Contents", "ContentsHeading"))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("TOCSRS", fontName="SRS", fontSize=10, leading=17)]
    story.append(toc)
    payload = document.model_dump()
    story.append(PageBreak())
    for index, section in enumerate(SECTION_SCHEMAS, start=1):
        story += [
            CondPageBreak(65 * mm),
            Spacer(1, 6 * mm),
            para(f"{index}. {_label(section)}", "SectionHeading"),
        ]
        if section == "introduction":
            story += [
                para("Original project description", "SubheadingSRS"),
                para(document.original_description),
            ]
        value_rows(payload[section])
    for label, data in [
        (
            "SDLC rankings and decision evidence",
            {
                "policy": document.sdlc_policy_version,
                "generation_profile": document.sdlc_prompt_version,
                "factors": payload["sdlc_factors"],
                "ranked_candidates": payload["sdlc_candidates"],
            },
        ),
        ("Evidence register", payload["evidence"]),
        (
            "Source references",
            [
                {key: value for key, value in source.items() if key != "text"}
                for source in payload["sources"]
            ],
        ),
        ("Validation findings", version["quality"]["findings"]),
        ("Human review history", reviews),
        (
            "AI drafting record",
            {
                "requested_model": document.requested_model_name,
                "actual_models_used": document.models_used,
                "section_models": document.section_models,
                "prompt_version": document.prompt_version,
            },
        ),
    ]:
        story += [CondPageBreak(65 * mm), Spacer(1, 6 * mm), para(label, "SectionHeading")]
        value_rows(data)
    story += [PageBreak(), para("Requirements traceability matrix", "SectionHeading")]
    matrix = [[para("Requirement"), para("Evidence / sources"), para("Stories / tests / SDLC")]]
    for row in version["quality"]["traceability"]:
        matrix.append(
            [
                para(row["requirement_id"]),
                para(", ".join(row["evidence_ids"] + row["source_chunks"]) or "Proposed"),
                para(", ".join(row["scenario_ids"] + row["test_ids"] + row["sdlc_phases"])),
            ]
        )
    table = Table(matrix, colWidths=[28 * mm, 63 * mm, 77 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5f2ee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5d1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story += [
        table,
        Spacer(1, 10 * mm),
        para(f"Model: {document.model_name}; prompt: {document.prompt_version}"),
    ]
    output = BytesIO()
    template = SRSDocTemplate(
        output,
        pagesize=(210 * mm, 297 * mm),
        leftMargin=21 * mm,
        rightMargin=21 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title=document.title,
        author="CyberSRS",
    )

    def page(canvas, doc):
        canvas.saveState()
        canvas.setFont("SRS", 7)
        canvas.setFillColor(colors.HexColor("#526a62"))
        canvas.drawString(21 * mm, 12 * mm, f"CyberSRS | Version {version['sequence']}")
        canvas.drawRightString(189 * mm, 12 * mm, f"{status} | {doc.page}")
        canvas.restoreState()

    template.addPageTemplates(
        PageTemplate(
            id="SRS",
            frames=[Frame(21 * mm, 22 * mm, 168 * mm, 253 * mm, id="body")],
            onPage=page,
        )
    )
    template.multiBuild(story)
    return output.getvalue()
