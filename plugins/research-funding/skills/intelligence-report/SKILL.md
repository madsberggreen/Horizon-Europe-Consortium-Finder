---
name: intelligence-report
description: Generates a Proposal Intelligence report — a structured EU research briefing covering key policy documents, European expert networks (including COST Actions), a portfolio of relevant projects, EU policy-making bodies, and brokerage events for a research theme or Horizon Europe topic. Use when asked for a proposal intelligence report, EU research briefing, policy landscape overview, or topic brief ("lav en proposal intelligence rapport om X", "hvad er det EU-politiske landskab for Z"). Output is a formatted PDF, no branding.
---

# Proposal Intelligence Report

A one-page (A4) PDF mapping the EU policy landscape for a research theme, in five sections. Dense, link-rich, authoritative.

## Anchor

**In the pipeline this skill runs AFTER call-matching.** Read the researcher's latest `calls/*.md` and anchor all five sections on the top 3–5 matched calls and their expected outcomes — not the researcher's general field. Standalone (no calls file): anchor on the theme the user gives, or ask for it.

## Check the theme cache first (do this before any web research)

All five sections describe a **theme landscape**, not a person — two researchers in the same subtheme need the same policy documents, COST Actions, DGs and brokerage events. Check whether it already exists:

```bash
python "<skill-dir>/scripts/theme_cache.py" --root "<workspace>/themes" \
    resolve "kw1" "kw2" ... --cluster HORIZON-CL2
```

- **exit 0 (FRESH)** — reuse. Do no web research; run `fetch` and stop after the strategic framing:
  ```bash
  python "<skill-dir>/scripts/theme_cache.py" --root "<workspace>/themes" fetch \
      --slug <slug> --kind intelligence --researcher "[Name]" \
      --out "researchers/[Name]/intelligence/[name]-intelligence-[YYYY-MM-DD].md"
  ```
  The fetched file carries a provenance banner. Regenerate the PDF from the copied `.json` sidecar so the researcher still gets a PDF in their folder.
- **exit 3 (STALE/MISSING)** — research fresh as below, then `store --slug <slug> --kind intelligence` both the `.md` and the `report_data.json`.
- **exit 4 (no match)** — research fresh, then register the subtheme with `new` and store. Keep subthemes narrower than a cluster: CL2 alone spans didactics, democracy and heritage, which share no policy landscape.

Override with `--ttl 0` when the user explicitly wants everything regenerated.

## Research (web search; prioritise ec.europa.eu, europarl.europa.eu, cordis.europa.eu, consilium.europa.eu, cost.eu — accuracy over volume)

1. **KEY DOCUMENTS** (6–9): relevant SDG(s), Commission strategic priority, DG R&I topic page, other responsible DGs, Council Conclusions, EP reports/resolutions, High-Level Expert Groups, JRC foresight.
2. **EUROPEAN EXPERT NETWORKS** — **COST Actions ALWAYS first (hard requirement).** Search cost.eu with 2–3 topic keywords; include code, status (Open/Closed/Upcoming), country count, URL `https://www.cost.eu/actions/CAXXXXX/`. If none open, list the most recent closed one and note the gap; if none at all, state "No active COST Action — potential opportunity to propose a new Action." Then: Partnerships, Joint Undertakings, ERICs, ERA-NETs, EIT-KICs, alliances.
3. **PORTFOLIO OF PROJECTS** (4–6): 2–4 HEU/H2020 + 1–2 FP7 from CORDIS; one-sentence description each.
4. **IMPACT ON EU POLICY-MAKING**: responsible DG unit(s), Council configuration + working party, lead EP committee(s) (full names), relevant agencies.
5. **BROKERAGE EVENTS & PARTNER SEARCH** (4–6): upcoming dated matchmaking events (F&T Portal event calendar, NCP calendars — include date, location, registration URL; at least one dated event), plus EEN (een.ec.europa.eu), NCP Portal (horizoneuropencpportal.eu), EuroCenter for Danish researchers (eusupport.dk), ERA-LEARN if relevant.

**Link rule:** every entry must have a working URL — omit any entry whose URL you cannot find. No placeholders.

## Produce and render

Write `report_data.json` using the schema in `scripts/generate_pdf.py` (title lines, optional `call_context`, `sections` with `entries` = {title, description, url}; PORTFOLIO and POLICY-IMPACT use `subsections`). Then:

```bash
python "<skill-dir>/scripts/generate_pdf.py" report_data.json \
    "researchers/[Name]/intelligence/[name]-intelligence-[YYYY-MM-DD].pdf"
```

(`pip install reportlab --break-system-packages` if missing.)

**The PDF is the deliverable — the run is not complete until it exists in the researcher's `intelligence/` folder** (never a temp dir), is >10 KB, and opens as a valid PDF. Also save the markdown summary alongside it, with every reference as a `[text](URL)` link.

Single-page priority: if content overflows, trim Brokerage Events to 3, then Portfolio to 4, then shorten descriptions.

Quality gate before delivery: COST Actions first in Section 2; institutional names accurate; project titles findable on CORDIS; at least one dated brokerage event; title uppercase.
