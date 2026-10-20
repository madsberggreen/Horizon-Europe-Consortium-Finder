# research-funding v2.1.0

Consolidated Horizon Europe pipeline — single source of truth replacing both the old plugin (v1.3.0) and the standalone skill copies.

## What changed in v2.1.0

- **CORDIS data downloads itself.** `cordis-analysis/scripts/download_cordis.py` fetches the official CORDIS Horizon Europe extracts from https://cordis.europa.eu/data/ into `<workspace>/cordis-data/` on first use and refreshes them when older than 30 days. `/add-researcher` and `/update-profiles` run it as step 0, so nobody has to update CORDIS files by hand. The download date is recorded in `cordis-data/SOURCE.txt`.
- **Works in a new, empty workspace.** The profile template ships in `templates/profil.md`, and the theme cache starts empty instead of failing when `themes/_taxonomy.json` does not exist yet.
- Removed `html-report/reference-layout-2026-04-15.html` (unused; contained a real researcher's briefing).

## What changed from v1.3.0

- **One skill set.** After installing this plugin, uninstall the standalone duplicates (researcher-profiling, profile-update, proposal-intelligence, horizon-europe-call-matching, cordis-consortium-analysis, html-briefing-report, wp-lead-pitch) in Settings → Capabilities. Their content now lives here.
- **Reordered pipeline.** /add-researcher now runs: profile → call-matching → Proposal Intelligence (anchored on matched calls) → CORDIS (capped at one thematic run) → pitch letters → HTML report. Previously PI ran before matching and could never anchor on real calls.
- **Deterministic code extracted to scripts.** API fetch, CORDIS pandas analysis, both PDF generators, the HTML renderer, and all verifiers are now `scripts/*.py` inside each skill. Claude no longer re-writes this code per run — SKILL.md files shrank ~60% and layouts are now literally frozen.
- **HTML layout enforced, not requested.** `html-report/scripts/build_report.py` contains the canonical 2026-04-15 design; Claude produces a content JSON only. Link verification is built into the renderer (hard fail).
- **Pitch letter format lives only in wp-pitch.** html-report renders letters from `pitches/*.md`; the duplicated ~800-word spec was removed.
- **Filenames standardised**: always `YYYY-MM-DD`, never overwrite.
- **/researcher-match retired** — superseded by /add-researcher (it duplicated the flow with contradictory pause rules).

## Install

See the README at the root of this repository.
