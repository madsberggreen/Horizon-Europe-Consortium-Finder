#!/usr/bin/env python3
"""Render the call-matching PDF from a scored-calls JSON. Layout is frozen here —
do not restyle per run.

Usage:
    python generate_calls_pdf.py scored_calls.json output.pdf

Input JSON schema:
{
  "researcher": "Name", "institution": "VIA University College",
  "generated": "YYYY-MM-DD",
  "shortlist": [                      # score >= 14, sorted desc
    {"identifier": "...", "title": "...", "url": "...", "score": 17,
     "cluster": "...", "instrument": "RIA", "status": "OPEN",
     "deadline": "YYYY-MM-DD", "budget": "EUR 12.0M",
     "deadline_flag": "" | "Closing in <60 days — partner entry only",
     "rationale": "2-4 sentences; [text](url) links allowed",
     "policy_support": [{"title": "...", "url": "..."}],
     "wp_role": "Suggested WP role"}
  ],
  "monitoring": [ {"identifier","title","url","score","deadline"} ]   # 10-13
}
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
GREEN = colors.HexColor("#16A34A")
AMBER = colors.HexColor("#D97706")
PURPLE = colors.HexColor("#7C3AED")
LIGHT_PURPLE = colors.HexColor("#F3F0FF")
LIGHT_BLUE = colors.HexColor("#EFF4FF")
GREY = colors.HexColor("#64748B")
LIGHT_GREY = colors.HexColor("#F8FAFC")

styles = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("t", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=13, textColor=colors.white),
    "sub": ParagraphStyle("s", parent=styles["Normal"], fontName="Helvetica-Bold",
                          fontSize=9.5, textColor=EU_GOLD),
    "sub2": ParagraphStyle("s2", parent=styles["Normal"], fontName="Helvetica-Oblique",
                           fontSize=8.5, textColor=colors.HexColor("#BFD3FF")),
    "body": ParagraphStyle("b", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=11),
    "rationale": ParagraphStyle("r", parent=styles["Normal"], fontName="Helvetica-Oblique",
                                fontSize=8, leading=11),
    "small": ParagraphStyle("sm", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=7, leading=9.5, textColor=GREY),
    "badge": ParagraphStyle("bg", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=11, textColor=colors.white, alignment=1),
}


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;")


def md_links_to_rl(text, color="#003399"):
    """Convert markdown [text](url) to ReportLab <a> markup; escape the rest."""
    parts, pos = [], 0
    for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text or ""):
        parts.append(esc(text[pos:m.start()]))
        parts.append(f'<a href="{m.group(2)}" color="{color}"><u>{esc(m.group(1))}</u></a>')
        pos = m.end()
    parts.append(esc((text or "")[pos:]))
    return "".join(parts)


def lnk(url, text, color="#003399"):
    return f'<a href="{url}" color="{color}"><u>{esc(text)}</u></a>'


def build(data, out_path):
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=15 * mm,
                            rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    W = A4[0] - 30 * mm
    el = []

    # Header: 3-row blue gradient
    hdr = Table([
        [Paragraph("CALL MATCHING — HORIZON EUROPE", S["title"])],
        [Paragraph(f"{esc(data['researcher'])} · {esc(data.get('institution',''))}", S["sub"])],
        [Paragraph(f"Generated {esc(data.get('generated',''))} · Source: EU Funding &amp; Tenders API (verified)", S["sub2"])],
    ], colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), EU_BLUE), ("BACKGROUND", (0, 1), (0, 1), MID_BLUE),
        ("BACKGROUND", (0, 2), (0, 2), DARK_BLUE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    el.append(hdr)
    el.append(Spacer(1, 6 * mm))

    for c in data.get("shortlist", []):
        badge_color = GREEN if c["score"] >= 16 else AMBER
        title_cell = Paragraph(
            f"{lnk(c['url'], c['identifier'])}<br/>"
            f"<b>{lnk(c['url'], c['title'])}</b><br/>"
            f"<font size=7 color=#64748B>{esc(c.get('cluster',''))} · {esc(c.get('instrument','See portal'))}"
            f" · {esc(c.get('status',''))} · Deadline {esc(c.get('deadline',''))} · {esc(c.get('budget','See portal'))}</font>",
            S["body"])
        head = Table([[Paragraph(f"{c['score']}/20", S["badge"]), title_cell]],
                     colWidths=[16 * mm, W - 16 * mm])
        head.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), badge_color), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (1, 0), (1, 0), 8), ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        el.append(head)

        # Match-strength bar
        frac = max(0.02, min(1.0, c["score"] / 20.0))
        bar = Table([["", ""]], colWidths=[W * frac, W * (1 - frac)], rowHeights=[1.6 * mm])
        bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), badge_color),
                                 ("BACKGROUND", (1, 0), (1, 0), LIGHT_GREY)]))
        el.append(bar)

        rows = [[Paragraph(md_links_to_rl(c.get("rationale", ""), "#7C3AED"), S["rationale"])]]
        if c.get("deadline_flag"):
            rows.append([Paragraph(f"<b>Timing:</b> {esc(c['deadline_flag'])}", S["small"])])
        if c.get("policy_support"):
            links = " · ".join(lnk(p["url"], p["title"], "#7C3AED") for p in c["policy_support"] if p.get("url"))
            rows.append([Paragraph(f"<b>Policy support:</b> {links}", S["small"])])
        if c.get("wp_role"):
            rows.append([Paragraph(f"<b>Suggested WP role:</b> {esc(c['wp_role'])}", S["body"])])
        rows.append([Paragraph(f"<b>Portal:</b> {lnk(c['url'], 'topic page on EU Funding & Tenders Portal')}", S["small"])])
        card = Table(rows, colWidths=[W])
        card.setStyle(TableStyle([
            # Row 0 = rationale box: purple left border, light purple background
            ("BACKGROUND", (0, 0), (0, 0), LIGHT_PURPLE),
            ("LINEBEFORE", (0, 0), (0, 0), 2, PURPLE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        el.append(card)
        el.append(Spacer(1, 4 * mm))

    mon = data.get("monitoring", [])
    if mon:
        el.append(Spacer(1, 2 * mm))
        el.append(Paragraph("<b>MONITORING LIST (score 10–13)</b>", S["body"]))
        rows = [[Paragraph("<b>Call</b>", S["small"]), Paragraph("<b>Score</b>", S["small"]),
                 Paragraph("<b>Deadline</b>", S["small"])]]
        for c in mon:
            rows.append([Paragraph(f"{lnk(c['url'], c['identifier'])} — {esc(c['title'][:80])}", S["small"]),
                         Paragraph(str(c["score"]), S["small"]), Paragraph(esc(c.get("deadline", "")), S["small"])])
        t = Table(rows, colWidths=[W - 40 * mm, 15 * mm, 25 * mm])
        t.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        el.append(t)

    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph(
        f"Research Funding Intelligence Pipeline · {esc(data.get('institution',''))} · Generated {esc(data.get('generated',''))}",
        S["small"]))
    doc.build(el)


def verify(out_path, n_shortlist):
    """Fail loudly if the PDF is missing, tiny, or under-linked."""
    import os
    assert os.path.exists(out_path), f"PDF not created: {out_path}"
    assert os.path.getsize(out_path) > 3_000, "PDF suspiciously small (<3 KB) — likely empty"
    try:
        import pypdf
        reader = pypdf.PdfReader(out_path)
        annots = sum(
            1 for page in reader.pages for a in (page.get("/Annots") or [])
            if (a.get_object() if hasattr(a, "get_object") else a).get("/Subtype") == "/Link")
        expected = n_shortlist * 2  # linked identifier + linked title per call
        assert annots >= expected, f"Only {annots} link annotations, expected >= {expected}"
    except ImportError:
        print("WARN: pypdf not installed — link-annotation check skipped")
    print(f"PDF verified: {out_path}")


if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    build(data, sys.argv[2])
    verify(sys.argv[2], len(data.get("shortlist", [])))
