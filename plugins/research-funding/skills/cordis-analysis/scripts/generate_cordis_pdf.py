#!/usr/bin/env python3
"""Render the CORDIS consortium-analysis PDF from a structured JSON. Layout frozen —
matches the Proposal Intelligence visual style (EU Blue header, purple accents).

Usage:
    python generate_cordis_pdf.py cordis_report.json output.pdf

Input JSON schema (Claude produces this from analyse_cordis.py output + judgment):
{
  "researcher": "...", "institution": "...", "theme": "...", "generated": "YYYY-MM-DD",
  "typical_winner_profile": "2-3 sentences",
  "coordinators": [{"name","url","country","type","relevance_note"}],       # section 1
  "projects": [{"acronym","url","programme","coordinator","period","budget"}],  # section 2
  "gaps": [{"gap","contribution"}],                                          # section 3
  "events": [{"title","url","date_location","note","primary": true|false}],  # section 4
  "targets": [{"name","url","country","reason"}],                            # section 5
  "strategic_assessment": "markdown-linked paragraph"
}
No emoji anywhere (Helvetica has no glyphs). Country codes as text (DK, DE...).
"""
import json
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

EU_BLUE = colors.HexColor("#003399")
MID_BLUE = colors.HexColor("#1A4A8C")
DARK_BLUE = colors.HexColor("#1A3A7A")
EU_GOLD = colors.HexColor("#FFCC00")
PURPLE = colors.HexColor("#7C3AED")
LIGHT_PURPLE = colors.HexColor("#F5F3FF")
LIGHT_GREY = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#E2E8F0")

styles = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("t", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=13, textColor=colors.white),
    "sub": ParagraphStyle("s", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9.5, textColor=EU_GOLD),
    "sub2": ParagraphStyle("s2", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=8.5, textColor=colors.HexColor("#BFD3FF")),
    "h": ParagraphStyle("h", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, textColor=EU_BLUE, spaceBefore=8, spaceAfter=2),
    "body": ParagraphStyle("b", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=11),
    "small": ParagraphStyle("sm", parent=styles["Normal"], fontName="Helvetica", fontSize=7, leading=9.5, textColor=colors.HexColor("#64748B")),
}


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;")


def lnk(url, text, color="#2563EB"):
    return f'<a href="{url}" color="{color}"><u>{esc(text)}</u></a>' if url else esc(text)


def md_links(text, color="#2563EB"):
    parts, pos = [], 0
    for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text or ""):
        parts.append(esc(text[pos:m.start()]))
        parts.append(lnk(m.group(2), m.group(1), color))
        pos = m.end()
    parts.append(esc((text or "")[pos:]))
    return "".join(parts)


def heading(el, text, W):
    el.append(Paragraph(text, S["h"]))
    rule = Table([[""]], colWidths=[W], rowHeights=[0.6 * mm])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), EU_BLUE)]))
    el.append(rule)
    el.append(Spacer(1, 2 * mm))


def styled_table(rows, widths):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def build(d, out_path):
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=15 * mm,
                            rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    W = A4[0] - 30 * mm
    el = []

    hdr = Table([
        [Paragraph("CORDIS CONSORTIUM ANALYSIS — HORIZON EUROPE", S["title"])],
        [Paragraph(f"{esc(d['researcher'])} · {esc(d.get('institution',''))}", S["sub"])],
        [Paragraph(f"{esc(d.get('theme',''))} · Generated {esc(d.get('generated',''))}", S["sub2"])],
    ], colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), EU_BLUE), ("BACKGROUND", (0, 1), (0, 1), MID_BLUE),
        ("BACKGROUND", (0, 2), (0, 2), DARK_BLUE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    el.append(hdr)
    el.append(Spacer(1, 4 * mm))

    if d.get("typical_winner_profile"):
        el.append(Paragraph(f"<b>Typical winner profile:</b> {md_links(d['typical_winner_profile'])}", S["body"]))

    heading(el, "1 · TYPICAL COORDINATORS &amp; WINNING INSTITUTIONS", W)
    rows = [[Paragraph(f"<b>{h}</b>", S["small"]) for h in ("Institution", "Country", "Type", "Relevance")]]
    for c in d.get("coordinators", []):
        rows.append([Paragraph(lnk(c.get("url"), c["name"]), S["body"]),
                     Paragraph(esc(c.get("country", "")), S["body"]),
                     Paragraph(esc(c.get("type", "")), S["body"]),
                     Paragraph(md_links(c.get("relevance_note", "")), S["small"])])
    el.append(styled_table(rows, [W * 0.34, W * 0.08, W * 0.18, W * 0.40]))

    heading(el, "2 · PORTFOLIO OF RELEVANT CORDIS PROJECTS", W)
    rows = [[Paragraph(f"<b>{h}</b>", S["small"]) for h in ("Project", "Programme", "Coordinator", "Period", "Budget")]]
    for p in d.get("projects", []):
        rows.append([Paragraph(lnk(p.get("url"), p["acronym"]), S["body"]),
                     Paragraph(esc(p.get("programme", "")), S["body"]),
                     Paragraph(esc(p.get("coordinator", "")), S["body"]),
                     Paragraph(esc(p.get("period", "")), S["body"]),
                     Paragraph(esc(p.get("budget", "")), S["body"])])
    el.append(styled_table(rows, [W * 0.20, W * 0.18, W * 0.34, W * 0.14, W * 0.14]))

    heading(el, "3 · CONSORTIUM GAPS — WHAT THE RESEARCHER CAN CONTRIBUTE", W)
    rows = [[Paragraph("<b>Gap identified</b>", S["small"]), Paragraph("<b>Contribution</b>", S["small"])]]
    for gp in d.get("gaps", []):
        rows.append([Paragraph(md_links(gp["gap"]), S["body"]),
                     Paragraph(md_links(gp["contribution"]), S["body"])])
    el.append(styled_table(rows, [W * 0.5, W * 0.5]))

    if d.get("events"):
        heading(el, "4 · BROKERAGE EVENTS &amp; PARTNER SEARCH", W)
        for ev in d["events"]:
            bg = LIGHT_PURPLE if ev.get("primary") else colors.white
            tag = "[PRIMARY] " if ev.get("primary") else ""
            card = Table([[Paragraph(
                f"<b>{tag}{lnk(ev.get('url'), ev['title'], '#7C3AED')}</b><br/>"
                f"{esc(ev.get('date_location',''))} — {md_links(ev.get('note',''), '#7C3AED')}", S["body"])]],
                colWidths=[W])
            card.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 2, PURPLE),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            el.append(card)
            el.append(Spacer(1, 1.5 * mm))

    heading(el, "5 · RECOMMENDED PARTNER SEARCH TARGETS", W)
    rows = [[Paragraph("<b>#</b>", S["small"]), Paragraph("<b>Institution</b>", S["small"]),
             Paragraph("<b>Country</b>", S["small"]), Paragraph("<b>Reason for contact</b>", S["small"])]]
    for i, t in enumerate(d.get("targets", []), 1):
        rows.append([Paragraph(str(i), S["body"]),
                     Paragraph(lnk(t.get("url"), t["name"]), S["body"]),
                     Paragraph(esc(t.get("country", "")), S["body"]),
                     Paragraph(md_links(t.get("reason", "")), S["small"])])
    el.append(styled_table(rows, [W * 0.05, W * 0.33, W * 0.09, W * 0.53]))

    if d.get("strategic_assessment"):
        el.append(Spacer(1, 3 * mm))
        card = Table([[Paragraph(f"<b>STRATEGIC ASSESSMENT — {esc(d['researcher'])}</b><br/>"
                                 + md_links(d["strategic_assessment"]), S["body"])]], colWidths=[W])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_PURPLE),
            ("LINEBEFORE", (0, 0), (0, -1), 2, PURPLE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        el.append(card)

    el.append(Spacer(1, 5 * mm))
    el.append(Paragraph(f"Research Funding Intelligence Pipeline · {esc(d.get('institution',''))} · "
                        f"Generated {esc(d.get('generated',''))} · For internal use only", S["small"]))
    doc.build(el)


def verify(out_path):
    import os
    assert os.path.exists(out_path), f"PDF not created: {out_path}"
    assert os.path.getsize(out_path) > 3_000, "PDF suspiciously small (<3 KB) — likely empty"
    print(f"PDF verified: {out_path}")


if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    build(data, sys.argv[2])
    verify(sys.argv[2])
