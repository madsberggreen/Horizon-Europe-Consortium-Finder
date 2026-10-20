#!/usr/bin/env python3
"""
Proposal Intelligence PDF Generator
Usage: python generate_pdf.py <input_json> <output_pdf>

Generates a formatted single-page Proposal Intelligence report PDF
matching the standard EU grant consulting briefing format.
"""

import json
import sys
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    KeepTogether, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY        = HexColor("#1F3864")   # title box background
SECTION_BLUE = HexColor("#2F5597")  # section heading text + rule
LINK_BLUE   = HexColor("#1155CC")   # hyperlink colour
RULE_GREY   = HexColor("#AAAAAA")   # footer rule
TEXT_BLACK  = HexColor("#000000")

# ── Page geometry ─────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN_L = 1.8 * cm
MARGIN_R = 1.8 * cm
MARGIN_T = 1.5 * cm
MARGIN_B = 1.5 * cm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


class TitleBox(Flowable):
    """Dark navy rectangle with white centred uppercase title text."""

    def __init__(self, line1, line2=None, width=CONTENT_W):
        Flowable.__init__(self)
        self.line1 = line1
        self.line2 = line2
        self.width = width
        # Determine height based on number of lines
        self.height = 1.35 * cm if not line2 else 1.9 * cm

    def draw(self):
        c = self.canv
        # Background rectangle
        c.setFillColor(NAVY)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Text
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 11)

        if self.line2:
            # Two-line title
            c.drawCentredString(self.width / 2, self.height - 0.75 * cm, self.line1)
            c.drawCentredString(self.width / 2, self.height - 1.35 * cm, self.line2)
        else:
            # Single-line title
            c.drawCentredString(self.width / 2, self.height / 2 - 0.16 * cm, self.line1)

    def wrap(self, availWidth, availHeight):
        return self.width, self.height


class SectionHeading(Flowable):
    """Section heading: small uppercase blue text + full-width rule below."""

    def __init__(self, text, width=CONTENT_W):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = 0.52 * cm

    def draw(self):
        c = self.canv
        c.setFillColor(SECTION_BLUE)
        c.setFont("Helvetica", 7.5)
        c.drawString(0, 0.22 * cm, self.text)
        # Rule below
        c.setStrokeColor(SECTION_BLUE)
        c.setLineWidth(0.5)
        c.line(0, 0.06 * cm, self.width, 0.06 * cm)

    def wrap(self, availWidth, availHeight):
        return self.width, self.height


def build_styles():
    """Return a dict of named ParagraphStyles."""
    base = getSampleStyleSheet()

    styles = {}

    styles["entry"] = ParagraphStyle(
        "entry",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_BLACK,
        spaceAfter=1.5,
        leftIndent=0,
    )

    styles["project_italic"] = ParagraphStyle(
        "project_italic",
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_BLACK,
        spaceBefore=3,
        spaceAfter=1,
    )

    styles["subsection_bold"] = ParagraphStyle(
        "subsection_bold",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_BLACK,
        spaceBefore=3,
        spaceAfter=1,
    )

    return styles


def make_link(text, url):
    """Return HTML for a hyperlink, or plain text if no URL."""
    if url:
        escaped = url.replace("&", "&amp;")
        return f'<link href="{escaped}"><u><font color="#1155CC">{text}</font></u></link>'
    return text


def render_entry_new(entry, styles):
    """Render an entry with new title/description/url schema.
    Output: bold linked title — description
    """
    title = entry.get("title", "")
    desc = entry.get("description", "")
    url = entry.get("url", "")
    title_html = make_link(f"<b>{title}</b>", url) if title else ""
    if title_html and desc:
        text = f"{title_html} — {desc}"
    elif title_html:
        text = title_html
    else:
        text = desc
    return Paragraph(text, styles["entry"])


def render_entry_legacy(label, items, styles):
    """Render a legacy labelled entry row (bold label: item1 / item2 ...)"""
    parts = [f"<b>{label}</b>: "]
    linked = []
    for item in items:
        text = item.get("text", "")
        url = item.get("url", "")
        linked.append(make_link(text, url))
    parts.append(" / ".join(linked))
    return Paragraph("".join(parts), styles["entry"])


def render_project(project, styles):
    """Render a single project entry: ACRONYM (bold/linked): description"""
    acronym = project.get("acronym", "")
    desc = project.get("description", "")
    url = project.get("url", "")
    acronym_html = make_link(f"<b>{acronym}</b>", url)
    text = f"{acronym_html}: {desc}"
    return Paragraph(text, styles["entry"])


def is_new_schema(entry):
    """Detect whether an entry uses the new title/description/url schema."""
    return "title" in entry or "description" in entry


def build_story(data):
    """Convert parsed JSON data into a ReportLab story (list of Flowables)."""
    styles = build_styles()
    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    line1 = data.get("title_line1", "PROPOSAL INTELLIGENCE")
    line2 = data.get("title_line2", None)
    story.append(TitleBox(line1, line2))
    story.append(Spacer(1, 0.25 * cm))

    # ── Sections ──────────────────────────────────────────────────────────────
    for section in data.get("sections", []):
        heading = section.get("heading", "")
        story.append(SectionHeading(heading))
        story.append(Spacer(1, 0.1 * cm))

        # Section with flat entries (KEY DOCUMENTS, EXPERT NETWORKS, BROKERAGE)
        if "entries" in section:
            for entry in section["entries"]:
                if is_new_schema(entry):
                    story.append(render_entry_new(entry, styles))
                else:
                    label = entry.get("label", "")
                    items = entry.get("items", [])
                    story.append(render_entry_legacy(label, items, styles))

        # Section with subsections (PORTFOLIO, POLICY IMPACT)
        elif "subsections" in section:
            for sub in section["subsections"]:
                # Support both old schema ("title") and new schema ("subheading")
                sub_title = sub.get("subheading", sub.get("title", ""))
                if "projects" in sub:
                    story.append(Paragraph(sub_title, styles["project_italic"]))
                    for proj in sub.get("projects", []):
                        story.append(render_project(proj, styles))
                else:
                    story.append(Paragraph(f"<b>{sub_title}</b>", styles["subsection_bold"]))
                    for entry in sub.get("entries", []):
                        if is_new_schema(entry):
                            story.append(render_entry_new(entry, styles))
                        else:
                            label = entry.get("label", "")
                            items = entry.get("items", [])
                            story.append(render_entry_legacy(label, items, styles))

        story.append(Spacer(1, 0.2 * cm))

    return story


def generate(input_json_path, output_pdf_path):
    """Main entry point: load JSON, build story, write PDF."""
    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title=data.get("title_line1", "Proposal Intelligence"),
    )

    story = build_story(data)

    # Footer callback
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(RULE_GREY)
        canvas.setLineWidth(0.5)
        y_rule = MARGIN_B - 0.3 * cm
        canvas.line(MARGIN_L, y_rule, PAGE_W - MARGIN_R, y_rule)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#666666"))
        canvas.drawString(MARGIN_L, y_rule - 0.32 * cm,
                          f"Proposal Intelligence Report")
        canvas.drawRightString(PAGE_W - MARGIN_R, y_rule - 0.32 * cm,
                               f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    print(f"PDF generated: {output_pdf_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_pdf.py <input.json> <output.pdf>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])
