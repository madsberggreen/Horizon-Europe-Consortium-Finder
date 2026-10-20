---
name: cordis-analysis
description: Analyses CORDIS project data to identify which organisations typically win Horizon Europe funding in a given topic area, and surfaces consortium partner candidates. Always outputs both a markdown summary AND a PDF in the researcher's cordis/ folder. Use when asked to analyse the consortium landscape, find potential partners, or run a CORDIS analysis for a call or researcher.
---

# CORDIS Consortium Analysis

Identifies which organisations win Horizon Europe funding in a topic area and surfaces consortium candidates, using five dimensions: relevance ratio, budget weighting, EU experience, geographic gap, Matthew effect. Input: call identifier(s), topic keywords, researcher profile. **Run at most once per thematic cluster** — if several shortlisted calls share a theme, one analysis covers them.

## Step 0 — Check the theme cache

Steps 1 and 2.1–2.4 describe a **theme landscape** (who wins here, typical consortium shape, power brokers, WP patterns) and are identical for every researcher in the subtheme. Only 2.3's geographic argument, 2.5's contacts and the strategic assessment are researcher-specific.

```bash
python "<skill-dir>/scripts/theme_cache.py" --root "<workspace>/themes" \
    resolve "kw1" "kw2" ... --cluster HORIZON-CL6
```

- **exit 0 (FRESH)** — `fetch --kind cordis --out "researchers/[Name]/cordis/[name]-cordis-[YYYY-MM-DD].md"`, then append/replace only the researcher-specific sections (GEOGRAPHIC GAP ANALYSIS, KEY CONTACTS, STRATEGIC ASSESSMENT) and regenerate the PDF. Skip Step 1 entirely.
- **exit 3 / exit 4** — run the full analysis below, then `store --slug <slug> --kind cordis` (both `.md` and the report JSON); register a new subtheme with `new` if there was no match.

## Step 1 — Run the data layer

CORDIS bulk files live in `<workspace>/cordis-data/`. First make sure they exist and are current (downloads the official EU extracts, ~55 MB zipped, on first use and when older than 30 days; otherwise does nothing):

```bash
python "<skill-dir>/scripts/download_cordis.py" --data-dir "<workspace>/cordis-data"
```

Then run:

```bash
python "<skill-dir>/scripts/analyse_cordis.py" \
    --data-dir "<workspace>/cordis-data" --out /tmp/cordis_analysis.json \
    --topic-code HORIZON-CL6 --country DK "keyword 1" "keyword 2"
```

The script does all joins (projects, organisations, topics, policyPriorities, deliverables, publications) and computes per organisation: projects-in-topic, coordinator count, EC contribution in topic, total HEU projects (EU experience), relevance ratio, power-broker flag (≥100 projects); plus country distribution with under-representation flag, policy-flag percentages, deliverable-type patterns, and publication-based warm-lead candidates. It prints a compact summary; detail is in the JSON.

If `download_cordis.py` exits 1 (no network access to cordis.europa.eu and no local copy), fall back to web search on cordis.europa.eu and prefix the output with: "⚠️ Based on web search — CORDIS bulk data could not be downloaded. Allow access to cordis.europa.eu, or download the four `cordis-HORIZON*-csv.zip` files from https://cordis.europa.eu/data/ and unzip them into `cordis-data/`." In the status message, state the CORDIS download date from `cordis-data/SOURCE.txt`.

## Step 2 — Interpret (the judgment steps)

From the script output plus targeted web searches:

1. **Typical winner profile** — 2–3 sentences on the consortium type that wins here.
2. **Top coordinator candidates (3–5)** — prefer high relevance ratio (specialists) or power brokers. For power brokers note: "difficult to out-compete as coordinator — approach as partner instead."
3. **Geographic argument** — if the researcher's country is <10% of consortia, formulate it explicitly ("DK appears in only X% — balance logic favours adding a Danish partner").
4. **Consortium gap** — which WP types smaller partners lead (from deliverable-type patterns), what thematic/methodological gap the researcher fills, which policy flag to frame the pitch around.
5. **Key contacts** — for each top candidate, web-search the project website/LinkedIn/institution for the PI or coordinator. Table: Name | Role | Institution | Contact | Source. Publicly available info only.

## Step 3 — Save outputs

**Link rule:** every organisation, project acronym, COST Action, and contact source is a markdown link (CORDIS project pages: `https://cordis.europa.eu/project/id/[ID]`). Verify with `python scripts/verify_links.py <file.md>` before saving.

1. **Markdown** → `researchers/[Name]/cordis/[name]-cordis-[YYYY-MM-DD].md` with sections: TYPICAL WINNER PROFILE, GEOGRAPHIC GAP ANALYSIS, TOP COORDINATOR CANDIDATES (ranked — the html-report skill reads the top 3 for pitch letters), MATTHEW EFFECT — POWER BROKERS, EU POLICY ALIGNMENT, WP OUTPUT PATTERNS, WARM CONTACT LEADS, KEY CONTACTS — OUTREACH TARGETS, STRATEGIC ASSESSMENT.
2. **PDF** — build the report JSON (schema at the top of the script; no emoji, country codes as text), then:

```bash
python "<skill-dir>/scripts/generate_cordis_pdf.py" cordis_report.json "researchers/[Name]/cordis/[name]-cordis-[YYYY-MM-DD].pdf"
```

The script owns the styling (matches the PI report) and verifies the file. The run is not complete until both files exist in the researcher's `cordis/` folder.
