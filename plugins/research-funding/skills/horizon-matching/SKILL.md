---
name: horizon-matching
description: Matches a researcher profile against open Horizon Europe calls and returns a ranked shortlist with scores and match rationale. Use when asked to find calls, match calls, identify funding opportunities, or run call-matching for a researcher.
---

# Horizon Europe Call Matching

Fetches live OPEN/FORTHCOMING Horizon Europe calls via the EU Funding & Tenders API, scores them against a researcher profile, and produces a Markdown shortlist + PDF. Requires the researcher's profile (keywords + thematic focus).

## Step 1 — Fetch verified calls

Derive 10–15 keywords from the profile (one per research area — fundable-topic phrases, not discipline labels). Then:

```bash
python "<skill-dir>/scripts/fetch_calls.py" --out /tmp/calls_verified.json "kw1" "kw2" ...
```

The script filters to OPEN/FORTHCOMING Horizon Europe only, dedupes, builds canonical topic URLs, parses budgets, infers clusters, and prints a compact `identifier | status | deadline | title` table.

**The identifiers in the output are the ONLY valid identifiers. Never invent or approximate a call.** If the sweep yields few matches, report that honestly — a short real list beats a long invented one.

## Step 2 — Two-stage triage (saves context)

1. From the printed table alone, pick the ~25 plausible candidates by title/cluster.
2. Read the `summary` field from the JSON **only for those candidates**.
3. WebFetch the portal topic page only for the final shortlist (score ≥ 14) to confirm scope and copy expected outcomes verbatim.

## Step 3 — Score 1–20, holistically

| Score | Meaning |
|---|---|
| 18–20 | Excellent — core keywords, methods, ambitions align tightly |
| 14–17 | Strong — substantial overlap → **shortlist** |
| 10–13 | Moderate → monitoring table |
| <10 | Discard silently |

Timing: if the deadline is <60 days away, add `deadline_flag`: "Closing in <60 days — partner entry only, too late to build a new consortium." Sort the shortlist by score, then deadline.

## Step 4 — Match rationale (the judgment step)

Per shortlisted call, 2–4 unique sentences that (a) name THIS call's specific scope/expected outcomes and (b) name the researcher's specific projects, methods, or publications that create the fit. **Advanced mode** (profile has an INTENDED DIRECTION section): include the `(idea)` keywords in the sweep, score fit to the idea as well as to the track record, and add one sentence per call on how the idea fits (or "fits the track record, not the idea"). Boilerplate ("strong overlap with digital themes") is forbidden. Every policy document or CORDIS project mentioned is a markdown link.

## Step 5 — Save outputs

**Link rule (applies to everything):** every identifier, title, and reference is a markdown link — canonical URL patterns are in `scripts/verify_links.py`. Run `python scripts/verify_links.py <file.md>` before saving; fix failures until clean.

1. **Markdown** → `researchers/[Name]/calls/[name]-calls-[YYYY-MM-DD].md`. Header line: `_Generated: [date] | Source: EU Funding & Tenders API (verified) | Keywords: [N] | Swept: [N] | Shortlisted: [N]_`. Per call: linked ID + linked title, cluster, instrument, status, deadline, budget, rationale, policy support links, suggested WP role. Include the verbatim expected outcomes of each shortlisted call (needed downstream by wp-pitch).
2. **PDF** — build the scored-calls JSON (schema documented at the top of the script), then:

```bash
python "<skill-dir>/scripts/generate_calls_pdf.py" scored_calls.json "researchers/[Name]/calls/[name]-calls-[YYYY-MM-DD].pdf"
```

The script owns all styling and verifies the PDF (exists, >10 KB, link annotations ≥ 2 per call). Never write ReportLab code by hand for this output.

Both files always use today's date (`YYYY-MM-DD`); never overwrite existing files.
