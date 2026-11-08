"""Readable PDF and Markdown for the IEEE 830 report view."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
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

from .schemas import Document
from .srs_presentation import build_srs_presentation


def _literal(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = re.sub(r"([`*_\[\]<>|])", r"\\\1", text)
    return re.sub(r"(?m)^(\s*)([#>+-]|[0-9]+[.)])", r"\1\\\2", text)


def render_srs_markdown(version: dict, status: str) -> str:
    """Render the concise outline without replacing any canonical requirement text."""
    report = build_srs_presentation(Document.model_validate(version["content"]))
    lines = [
        f"# {_literal(report.title)}",
        "",
        "Software Requirements Specification",
        "",
        "IEEE 830-1998 outline",
        "",
        status,
        "",
        f"Version {version['sequence']} | {version['created_at']}",
        "",
        "## Contents",
        "",
    ]
    lines.extend(f"- {section.number} {section.title}" for section in report.sections)
    for section in report.sections:
        lines.extend(
            ["", f"{'#' * (section.number.count('.') + 2)} {section.number} {section.title}", ""]
        )
        for text in section.paragraphs:
            lines.extend([_literal(text), ""])
        lines.extend(f"- {_literal(text)}" for text in section.bullets)
        for table in section.tables:
            lines.extend(
                [
                    "",
                    "| " + " | ".join(_literal(cell) for cell in table.columns) + " |",
                    "| " + " | ".join("---" for _ in table.columns) + " |",
                ]
            )
            lines.extend(
                "| " + " | ".join(_literal(cell).replace("\n", " ") for cell in row) + " |"
                for row in table.rows
            )
        for row in section.requirements:
            lines.extend(
                [
                    "",
                    f"**{_literal(row.id)}** · {row.priority.capitalize()} · {row.basis}",
                    "",
                    _literal(row.statement),
                    "",
                ]
            )
            for citation in row.sources:
                lines.append(f"Source {_literal(citation.chunk_id)}: {_literal(citation.quote)}")
            lines.append("Traceability: " + ", ".join(row.evidence_ids + row.test_ids))
    lines.extend(
        [
            "",
            "---",
            "",
            f"Canonical content SHA-256: {version['content_hash']}",
            "",
            "Detailed acceptance criteria, evidence, architecture and the SDLC plan "
            "are retained in the supporting report and canonical JSON.",
            "",
        ]
    )
    return "\n".join(lines)


class IEEEReportTemplate(BaseDocTemplate):
    """Produce a nested contents list and bookmarks for the numbered outline."""

    def afterFlowable(self, flowable) -> None:
        """Collect only report section headings for the contents pass."""
        number = getattr(flowable, "srs_number", None)
        if number is not None:
            level = number.count(".")
            key = "ieee-" + number.replace(".", "-")
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, level=level)
            self.notify("TOCEntry", (level, flowable.getPlainText(), self.page, key))


def render_srs_pdf(version: dict, status: str) -> bytes:
    """Render a concise A4 report with canonical IDs, readable tables and exact statements."""
    report = build_srs_presentation(Document.model_validate(version["content"]))
    font_root = Path(reportlab.__file__).parent / "fonts"
    for name, filename in (("SRS", "Vera.ttf"), ("SRS-Bold", "VeraBd.ttf")):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(font_root / filename)))
    pdfmetrics.registerFontFamily("SRS", normal="SRS", bold="SRS-Bold", italic="SRS")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("IEEEBody", fontName="SRS", fontSize=9, leading=13, spaceAfter=6))
    styles.add(ParagraphStyle("IEEESmall", parent=styles["IEEEBody"], fontSize=7, leading=10))
    styles.add(
        ParagraphStyle("IEEETitle", fontName="SRS-Bold", fontSize=23, leading=29, spaceAfter=16)
    )
    for level, size in enumerate((17, 12, 10)):
        styles.add(
            ParagraphStyle(
                f"IEEEHeading{level}",
                fontName="SRS-Bold",
                fontSize=size,
                leading=size + 5,
                spaceBefore=12 if level else 18,
                spaceAfter=7,
                keepWithNext=True,
                textColor=colors.HexColor("#12635c"),
            )
        )
    styles.add(
        ParagraphStyle("IEEEBullet", parent=styles["IEEEBody"], leftIndent=12, bulletIndent=2)
    )

    def para(text: str, style: str = "IEEEBody") -> Paragraph:
        return Paragraph(escape(text).replace("\n", "<br/>"), styles[style])

    story = [
        para(report.title, "IEEETitle"),
        para("Software Requirements Specification"),
        para("IEEE 830-1998 outline"),
        para(status),
        para(f"Version {version['sequence']} | {version['created_at']}", "IEEESmall"),
        Spacer(1, 4 * mm),
        para("Contents", "IEEEHeading1"),
    ]
    toc = TableOfContents(
        tableStyle=TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    toc.levelStyles = [
        ParagraphStyle(
            f"IEEETOC{level}",
            fontName="SRS",
            fontSize=8,
            leading=12,
            leftIndent=level * 10,
            firstLineIndent=0,
            spaceBefore=0,
        )
        for level in range(3)
    ]
    story.extend([toc, PageBreak()])
    for section in report.sections:
        if "." not in section.number:
            story.append(CondPageBreak(40 * mm))
        heading = para(
            f"{section.number} {section.title}", f"IEEEHeading{section.number.count('.')}"
        )
        heading.srs_number = section.number
        story.append(heading)
        story.extend(para(text) for text in section.paragraphs)
        story.extend(
            Paragraph(escape(text), styles["IEEEBullet"], bulletText="•")
            for text in section.bullets
        )
        for data in section.tables:
            width = 168 * mm / len(data.columns)
            table = Table(
                [[para(cell, "IEEESmall") for cell in row] for row in [data.columns] + data.rows],
                colWidths=[width] * len(data.columns),
                repeatRows=1,
                hAlign="LEFT",
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5f2ee")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5d1")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.extend([table, Spacer(1, 3 * mm)])
        for row in section.requirements:
            story.append(
                para(f"{row.id} · {row.priority.capitalize()} · {row.basis}", "IEEEHeading2")
            )
            story.append(para(row.statement))
            for citation in row.sources:
                story.append(para(f"Source {citation.chunk_id}: {citation.quote}", "IEEESmall"))
            story.append(
                para("Traceability: " + ", ".join(row.evidence_ids + row.test_ids), "IEEESmall")
            )
    story.extend(
        [
            Spacer(1, 6 * mm),
            para(
                "Detailed acceptance criteria, evidence, architecture and the SDLC plan are "
                "available in the supporting report and canonical JSON.",
                "IEEESmall",
            ),
            para(f"Canonical content SHA-256: {version['content_hash']}", "IEEESmall"),
        ]
    )
    output = BytesIO()
    template = IEEEReportTemplate(
        output,
        pagesize=(210 * mm, 297 * mm),
        leftMargin=21 * mm,
        rightMargin=21 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=report.title,
        author="CyberSRS",
    )

    def page(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("SRS", 7)
        canvas.setFillColor(colors.HexColor("#526a62"))
        canvas.drawString(21 * mm, 11 * mm, f"CyberSRS | IEEE 830-1998 | v{version['sequence']}")
        canvas.drawRightString(189 * mm, 11 * mm, f"{status} | {doc.page}")
        canvas.restoreState()

    template.addPageTemplates(
        PageTemplate(
            id="IEEE", frames=[Frame(21 * mm, 20 * mm, 168 * mm, 257 * mm, id="body")], onPage=page
        )
    )
    template.multiBuild(story)
    return output.getvalue()
