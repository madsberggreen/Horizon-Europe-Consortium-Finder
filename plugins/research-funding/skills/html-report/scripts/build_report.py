#!/usr/bin/env python3
"""Render the Researcher Briefing HTML from a content JSON. The layout (CSS, tabs,
components) is frozen in this script — identical on every run, per the canonical
reference layout of 2026-04-15. Claude produces ONLY the content JSON.

Usage:
    python build_report.py content.json output.html

content.json schema:
{
  "researcher": "Name", "subtitle": "Institution · Title · Generated YYYY-MM-DD",
  "footer_sources": "ORCID ..., institutional portal, CORDIS, EU Funding & Tenders Portal",
  "generated": "YYYY-MM-DD",
  "tabs": {                      # five fixed tabs, each a list of blocks
    "profile": [...], "intelligence": [...], "calls": [...],
    "partners": [...], "actions": [...]
  }
}

Block types (all text supports markdown links [t](u), **bold**, *italic*):
  {"type":"h3","text":...}
  {"type":"p","text":...}                       # optional "small": true
  {"type":"kv","items":[["Label","value"],...]}
  {"type":"ul","items":[...]} | {"type":"ol","items":[...]}   # items may nest: {"text":..., "sub":[...]}
  {"type":"table","headers":[...],"rows":[[...]]}             # cell strings; scores like "18/20" auto-badge
  {"type":"callout","text":...}
  {"type":"pills","items":[...]}
  {"type":"letter","n":1,"org":"Org","country":"NO","chips":["CORDIS #1","relevance 0.42"],
   "body":"full letter text, markdown links allowed, \\n\\n = paragraphs",
   "policy_note":"Policy argument based on: [Doc](url)","insufficient_data": false}

Link verification (bare URLs, unlinked HORIZON-* / CAxxxxx tokens) runs before
saving; the script refuses to write a failing file.
"""
import html
import json
import re
import sys

TAB_LABELS = [("profile", "Profile"), ("intelligence", "Proposal Intelligence"),
              ("calls", "Matched Calls"), ("partners", "Partner Institutions"),
              ("actions", "Action Plan")]

CSS = """
  :root { --primary:#003366; --primary-light:#E6EEF6; --accent:#C99A2E; --bg:#FAFAF7;
          --text:#1E1E1E; --muted:#666; --border:#D8D8D2; --purple:#7C3AED; --amber-bg:#FEF3C7; }
  * { box-sizing:border-box; }
  body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
         margin:0; background:var(--bg); color:var(--text); line-height:1.5; }
  header { background:var(--primary); color:white; padding:28px 40px; }
  header h1 { margin:0 0 6px; font-size:22px; font-weight:600; }
  header .meta { font-size:13px; opacity:.85; }
  nav.tabs { display:flex; gap:0; background:white; border-bottom:1px solid var(--border);
             padding:0 40px; overflow-x:auto; }
  nav.tabs button { background:none; border:none; padding:14px 20px; font-size:13px; font-weight:500;
                    cursor:pointer; color:var(--muted); border-bottom:3px solid transparent; white-space:nowrap; }
  nav.tabs button:hover { color:var(--primary); }
  nav.tabs button.active { color:var(--primary); border-bottom-color:var(--accent); font-weight:600; }
  main { padding:32px 40px; max-width:1100px; }
  section.pane { display:none; } section.pane.active { display:block; }
  h2 { color:var(--primary); font-size:18px; margin-top:0; border-bottom:2px solid var(--primary-light); padding-bottom:8px; }
  h3 { color:var(--primary); font-size:14px; margin-top:20px; }
  table { border-collapse:collapse; width:100%; margin:12px 0; font-size:13px; }
  th,td { border:1px solid var(--border); padding:8px 10px; text-align:left; vertical-align:top; }
  th { background:var(--primary-light); color:var(--primary); font-weight:600; }
  .kv { display:grid; grid-template-columns:180px 1fr; gap:6px 14px; font-size:13px; margin:10px 0 20px; }
  .kv dt { font-weight:600; color:var(--muted); } .kv dd { margin:0; }
  .score-badge { display:inline-block; background:var(--accent); color:white; font-weight:600;
                 padding:2px 8px; border-radius:10px; font-size:12px; margin-left:8px; }
  .score-secondary { background:#8a8a8a; }
  .callout { background:var(--primary-light); border-left:4px solid var(--primary);
             padding:14px 18px; margin:14px 0; border-radius:0 4px 4px 0; font-size:13px; }
  ul { padding-left:22px; } li { margin:4px 0; font-size:13px; }
  a { color:var(--primary); }
  .pill { display:inline-block; background:white; border:1px solid var(--border); padding:2px 8px;
          border-radius:10px; font-size:11px; margin:2px 4px 2px 0; color:var(--muted); }
  .letter { background:white; border:1px solid var(--border); border-radius:8px;
            box-shadow:0 1px 3px rgba(0,0,0,.1); margin:16px 0; overflow:hidden; }
  .letter-head { background:var(--primary-light); padding:12px 18px; font-weight:600; font-size:13px; color:var(--primary); }
  .letter-chips { padding:8px 18px 0; }
  .letter .draft { background:var(--amber-bg); color:#92400E; font-size:12px; padding:8px 18px; }
  .letter blockquote { margin:12px 18px; padding:10px 16px; border-left:3px solid var(--purple);
                       background:#F5F3FF; font-size:13px; white-space:pre-wrap; }
  .letter .policy-note { font-size:12px; color:var(--muted); padding:0 18px 12px; }
  .letter details summary { cursor:pointer; padding:8px 18px; font-size:13px; color:var(--primary); }
  .copy-btn { margin:0 18px 14px; padding:6px 14px; font-size:12px; cursor:pointer;
              background:var(--primary); color:white; border:none; border-radius:4px; }
  footer { padding:20px 40px; border-top:1px solid var(--border); font-size:11px; color:var(--muted); }
  @media print { nav.tabs, .copy-btn { display:none; } section.pane { display:block; } }
"""

JS = """
  const buttons=document.querySelectorAll('.tab-btn'),panes=document.querySelectorAll('.pane');
  buttons.forEach(btn=>btn.addEventListener('click',()=>{buttons.forEach(b=>b.classList.remove('active'));
    panes.forEach(p=>p.classList.remove('active'));btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');}));
  document.querySelectorAll('.copy-btn').forEach(b=>b.addEventListener('click',()=>{
    const t=b.closest('.letter').querySelector('blockquote').innerText;
    navigator.clipboard.writeText(t).then(()=>{b.textContent='Copied!';setTimeout(()=>b.textContent='Copy to clipboard',1500);});}));
"""


def fmt(text):
    """Escape HTML, then apply markdown links / **bold** / *italic*."""
    if text is None:
        return ""
    t = html.escape(str(text), quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def badge(cell):
    """Auto-render 'NN/20' score cells as badges (>=14 gold, else grey)."""
    m = re.fullmatch(r"(\d{1,2})/20", str(cell).strip())
    if not m:
        return fmt(cell)
    cls = "score-badge" if int(m.group(1)) >= 14 else "score-badge score-secondary"
    return f'<span class="{cls}">{m.group(0)}</span>'


def li(item):
    if isinstance(item, dict):
        sub = "".join(f"<li>{fmt(s)}</li>" for s in item.get("sub", []))
        return f"<li>{fmt(item.get('text',''))}<ul>{sub}</ul></li>" if sub else f"<li>{fmt(item.get('text',''))}</li>"
    return f"<li>{fmt(item)}</li>"


def render_block(b):
    t = b["type"]
    if t == "h3":
        return f"<h3>{fmt(b['text'])}</h3>"
    if t == "p":
        style = ' style="font-size:13px;"' if b.get("small") else ""
        return f"<p{style}>{fmt(b['text'])}</p>"
    if t == "kv":
        rows = "".join(f"<dt>{fmt(k)}</dt><dd>{fmt(v)}</dd>" for k, v in b["items"])
        return f'<dl class="kv">{rows}</dl>'
    if t in ("ul", "ol"):
        return f"<{t}>{''.join(li(i) for i in b['items'])}</{t}>"
    if t == "table":
        head = "".join(f"<th>{fmt(h)}</th>" for h in b["headers"])
        body = "".join("<tr>" + "".join(f"<td>{badge(c)}</td>" for c in row) + "</tr>"
                       for row in b["rows"])
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    if t == "callout":
        return f'<div class="callout">{fmt(b["text"])}</div>'
    if t == "pills":
        return "<div>" + "".join(f'<span class="pill">{fmt(p)}</span>' for p in b["items"]) + "</div>"
    if t == "letter":
        chips = "".join(f'<span class="pill">{fmt(c)}</span>' for c in b.get("chips", []))
        warn = ('<div class="draft">INSUFFICIENT CORDIS DATA — re-run the CORDIS analysis '
                'to populate this letter properly.</div>') if b.get("insufficient_data") else ""
        note = (f'<div class="policy-note">{fmt(b["policy_note"])}</div>'
                if b.get("policy_note") else "")
        return (f'<div class="letter">'
                f'<div class="letter-head">Pitch Letter {b.get("n","")} — {fmt(b.get("org",""))}, {fmt(b.get("country",""))}</div>'
                f'<div class="letter-chips">{chips}</div>'
                f'<div class="draft">DRAFT — review and personalise before sending</div>{warn}'
                f'<details open><summary>Letter text</summary>'
                f'<blockquote>{fmt(b.get("body",""))}</blockquote></details>'
                f'{note}<button class="copy-btn">Copy to clipboard</button></div>')
    raise ValueError(f"Unknown block type: {t}")


def verify_links(html_text):
    failures = []
    stripped = re.sub(r'(?:href|src)="[^"]*"', "", html_text)
    bare = re.findall(r'https?://[^\s<>"\')\]]+', stripped)
    if bare:
        failures.append(f"Bare URLs in visible text: {bare[:5]}")
    for pat, label in ((r"\bHORIZON-[A-Z0-9]+(?:-[A-Z0-9]+)+\b", "Topic ID"),
                       (r"\bCA\d{5}\b", "COST Action")):
        for tok in set(re.findall(pat, html_text)):
            if re.search(rf"(?<!>)\b{re.escape(tok)}\b(?![^<]*</a>)", html_text):
                failures.append(f"{label} not linked: {tok}")
    return failures


def build(data):
    tabs_nav, panes = [], []
    for i, (key, label) in enumerate(TAB_LABELS):
        active = " active" if i == 0 else ""
        tabs_nav.append(f'<button class="tab-btn{active}" data-tab="{key}">{label}</button>')
        blocks = "".join(render_block(b) for b in data["tabs"].get(key, []))
        panes.append(f'<section class="pane{active}" id="{key}"><h2>{label}</h2>{blocks}</section>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Researcher Briefing — {html.escape(data["researcher"])}</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>Researcher Briefing — {html.escape(data["researcher"])}</h1>
  <div class="meta">{fmt(data.get("subtitle",""))}</div>
</header>
<nav class="tabs">{''.join(tabs_nav)}</nav>
<main>
{''.join(panes)}
</main>
<footer>
  Generated by Research Funding Intelligence Pipeline · {html.escape(data.get("generated",""))} · Sources: {fmt(data.get("footer_sources",""))}
</footer>
<script>{JS}</script>
</body>
</html>"""


def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    out = build(data)
    failures = verify_links(out)
    if failures:
        print("LINK VERIFICATION FAILED — file NOT written:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Report written and link-verified: {sys.argv[2]}")


if __name__ == "__main__":
    main()
