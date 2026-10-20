# research-funding v2.6.0

Consolidated Horizon Europe pipeline — single source of truth replacing both the old plugin (v1.3.0) and the standalone skill copies.

## What changed in v2.6.0

- **Who is asking.** Under the researcher's name the form offers "I am working on behalf of this researcher" (default) or "That's me!". The request carries `Requested by: Advisor | Researcher`; with Researcher, the Action Plan in the HTML report addresses the researcher directly as "you" instead of an advisor. Pitch letters are unchanged.

## What changed in v2.5.1

- Display name **Horizon Europe Consortium Finder**, author Mads Lykke Berggreen (madsberggreen) and search keywords added to `plugin.json` and the marketplace entry, so the plugin can be found by those names. The technical name stays `research-funding`.

## What changed in v2.5.0

- **`/start` works in regular chats.** The form is embedded in `commands/start.md` itself; in a chat Claude can only read the command's own text, so the separate `start/form.html` was never found. The fallback no longer links to the old copy-and-paste page, and Claude is told not to render the form as an artifact (only the inline widget can send the request).
- The profile template moved to `skills/researcher-profiling/templates/profil.md` for the same reason.
- If the form is shown somewhere it can't send to the chat, the button copies the request instead and says so.

## What changed in v2.4.1

- Placeholders and examples no longer mention VIA. UCviden is searched only for researchers at VIA University College ("VIA", "VIA UC" or "VIA University College"); other institutions use their own public research portal.

## What changed in v2.4.0

- **`/start` command.** Shows the start form (`start/form.html`) inside the chat via the visualize widget. Pressing **Find me a consortium!** sends the request as the user's next message and the pipeline runs — no copy and paste. Falls back to plain-text questions where the chat cannot show widgets.

## What changed in v2.3.0

- **Simple and Advanced mode.** `/add-researcher` accepts the structured request built by the start page (`app/index.html`). Simple uses public data only and says so in every output. Advanced saves the user's idea and documents to `inbox/user-input-[date].md` and uses them in researcher-profiling (INTENDED DIRECTION section, `(idea)` keywords), horizon-matching (idea fit), intelligence-report (YOUR IDEA IN THIS LANDSCAPE section, never cached) and wp-pitch (concrete contribution to the quoted expected outcome).

## What changed in v2.2.0

- **Reports on request only.** `/update-profiles` is no longer a weekly scheduled sweep. It now only runs the onboarding pipeline for new researcher folders; inbox processing, re-matching, theme-cache refresh, report regeneration and the weekly status overview were removed.

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
