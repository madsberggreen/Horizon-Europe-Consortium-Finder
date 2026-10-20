---
description: Run the full researcher onboarding pipeline — profile, call-matching, Proposal Intelligence, CORDIS analysis, pitch letters, and HTML report — for a named researcher
---

# /add-researcher

Triggered by a researcher name (optionally + institution): "Tilføj Anne Mette Frost", "Ny forsker: Maria Jensen, AAU", "Kør pipeline på Søren Dam". Runs the whole flow **without pausing for confirmation** — unless the researcher cannot be identified unambiguously, in which case: leave the profile template empty, ask the user for ORCID/department, and stop.

## Modes

Requests built with the start page (`app/index.html` in the repository) look like this:

```
/add-researcher
Mode: Simple | Advanced
Name: …
Institution: …
ORCID: … (optional)
Research idea:
<<<
free text
>>>
Document: <file name>
<<<
extracted text
>>>
```

`Research idea` and `Document` blocks appear only in Advanced mode (zero or more documents). A request without a `Mode:` line is **Simple**. The in-chat form from `/start` sends the same format with `Find me a consortium!` as its first line instead of `/add-researcher`.

- **Simple** — public data only: ORCID, institutional pages, CORDIS, EU portals and web search. Do not read files in the researcher's folder. Every output states "Based on publicly available data only."
- **Advanced** — the user's idea and documents steer the whole run. Save them in step 1, then use them in profiling (step 2), call-matching (step 3), Proposal Intelligence (step 4) and pitch letters (step 6), as each skill's "Advanced mode" section describes. The user's material is confidential: use it to shape content, never quote it at length in outputs, and never copy evaluator comments from rejected applications into anything meant for third parties.

## Pipeline (this order is deliberate — PI runs AFTER matching so it anchors on real calls)

**0. CORDIS data check** — before anything else, run `python "${CLAUDE_PLUGIN_ROOT}/skills/cordis-analysis/scripts/download_cordis.py" --data-dir "<workspace>/cordis-data"` (the script sits in the `cordis-analysis` skill's `scripts/` folder). It downloads the official CORDIS extracts on first use and refreshes them when older than 30 days; otherwise it does nothing. Never ask the user to update CORDIS files by hand. If it exits 1, continue — step 5 falls back to web search.

**1. Folders** — create `researchers/[Name]/{inbox,profile,calls,cordis,intelligence,pitches,reports}/`; copy `researchers/_template/profil.md` in and set the name. If the workspace has no `researchers/_template/profil.md`, create it first from the plugin's `templates/profil.md`. **Advanced mode:** save the research idea and every document block verbatim to `inbox/user-input-[YYYY-MM-DD].md` (header `# User input — [Name]` / `_Mode: Advanced | Received: [date]_`, then `## Research idea` and one `## Document: [file name]` section per document).

**2. Profile** — run `researcher-profiling` in the request's mode (institution from the message, else ask; use the ORCID from the request when given). Mark auto-fetched data `_(auto-hentet [date])_`. Save `profile/[name]-profile.md` and fill `profil.md`.

**3. Call-matching** — run `horizon-matching` with the profile. Outputs `calls/[name]-calls-[YYYY-MM-DD].{md,pdf}`.

**4. Proposal Intelligence** — run `intelligence-report` anchored on the top 3–5 matched calls (the skill reads `calls/*.md` itself). It checks the theme cache first and reuses a landscape under 60 days old. Outputs `intelligence/[name]-intelligence-[YYYY-MM-DD].{json,md,pdf}`.

**5. CORDIS** — run `cordis-analysis` **once for the dominant thematic cluster of the shortlist** (twice only if the top calls split across two unrelated themes — never more). It also checks the theme cache first. Outputs `cordis/[name]-cordis-[YYYY-MM-DD].{md,pdf}`.

**6. Pitch letters** — run `wp-pitch` for each of the Top-3 CORDIS coordinator candidates against the best-matching call. Outputs in `pitches/`.

**7. HTML report** — run `html-report`. Output `reports/[name]-briefing-[YYYY-MM-DD].html` (link verification is built into the renderer).

**8. Status message** in chat: mode used (Simple: "Based on publicly available data only"; Advanced: which documents were used), profile summary (title, institution, core areas, ORCID), N calls matched + top match with score, PI themes mapped, N partner institutions found, links to the HTML report and PDFs, and any items awaiting manual verification (e.g. institutional HEU project links).

## Rules

- Never pause mid-run; never send emails or external messages without explicit approval; never modify an existing profile without a dated backup first.
- All filenames use today's date `YYYY-MM-DD`; never overwrite existing outputs.
- Order is fixed: matching before PI (PI anchors on matched calls); CORDIS capped at one thematic run.
- PI and CORDIS reuse the shared theme cache in `themes/` when the landscape is <60 days old; the researcher-specific assessment and all pitch letters are always generated fresh. Report in step 8 which artifacts were reused and how old they were.
