---
name: html-report
description: Converts pipeline outputs into a self-contained interactive HTML report with tabs for profile, intelligence, matched calls, collaboration institutions, and action plan. Use when asked to generate a report, briefing, or HTML output for a researcher.
---

# HTML Briefing Report

Renders a self-contained, offline HTML briefing from the researcher's pipeline files. **The layout is frozen inside `scripts/build_report.py`** (canonical 2026-04-15 design) — you produce only a content JSON; the script owns all CSS, tabs, components, and runs link verification before writing. Never hand-write the HTML.

## Inputs

Read the researcher's latest files (newest date wins): `profil.md` / `profile/*.md`, `intelligence/*.md`, `calls/*.md`, `cordis/*.md`, `pitches/*.md`.

## Build the content JSON

Schema and block types (`h3`, `p`, `kv`, `ul`/`ol`, `table`, `callout`, `pills`, `letter`) are documented at the top of `scripts/build_report.py`. Five fixed tabs — English labels are hardcoded in the script: Profile | Proposal Intelligence | Matched Calls | Partner Institutions | Action Plan.

Content rules per tab:

1. **profile** — kv block (name, title, institution, ORCID as link, career stage), research areas, methods, keyword pills, current projects, EU-funding history.
2. **intelligence** — the five PI sections; COST Actions first among networks; portfolio as a table with linked acronyms.
3. **calls** — scoring-note paragraph, top-matches table (score cells as "NN/20" — auto-badged), one "Why it fits" h3+ul per shortlisted call (policy anchors + recommended role), monitoring table. Call IDs and titles as markdown links to the topic page.
4. **partners** — headline callout, candidate tables (institution linked, country, evidence, role fit), consortium-gaps list, brokerage-events summary.
5. **actions** — time-phased to-do lists with concrete names and dates, a highest-leverage-action callout, and **exactly 3 `letter` blocks**, one per Top-3 organisation from the CORDIS "TOP COORDINATOR CANDIDATES" section:
   - Letter bodies come from `pitches/*.md` if present; otherwise invoke the **wp-pitch** skill to draft them (it owns the four-argument letter format — do not re-specify it here).
   - Fewer than 3 ranked organisations → still render 3 letter blocks, marking missing ones with `"insufficient_data": true`. Never silently drop a letter.
   - Each letter block: `chips` (CORDIS rank, relevance ratio, EU experience), `policy_note` linking the PI document cited.

All text fields support markdown links — every call ID, title, project acronym, COST Action, policy document, and institution must be a link. The script hard-fails the build on bare URLs or unlinked HORIZON-*/CAxxxxx tokens.

## Render

```bash
python "<skill-dir>/scripts/build_report.py" content.json \
    "researchers/[Name]/reports/[name]-briefing-[YYYY-MM-DD].html"
```

Always today's date in the filename; never overwrite an existing report. The file is fully self-contained (works from OneDrive/SharePoint double-click).
