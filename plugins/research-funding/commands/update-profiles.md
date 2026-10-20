---
description: Sweep all researcher inboxes for new files, update profiles, re-run call-matching, and regenerate HTML reports for any researchers with changes
---

# /update-profiles

Weekly combined update (scheduled Mondays 08:10, or run manually). Detects new researcher folders, processes inboxes, updates profiles, and regenerates reports for affected researchers. Runs autonomously — no mid-run confirmations.

## Phases

**0. CORDIS data check** — run `python "${CLAUDE_PLUGIN_ROOT}/skills/cordis-analysis/scripts/download_cordis.py" --data-dir "<workspace>/cordis-data"` (the script sits in the `cordis-analysis` skill's `scripts/` folder). It refreshes the CORDIS extracts when older than 30 days and otherwise does nothing. Report the CORDIS download date (from `cordis-data/SOURCE.txt`) in the weekly status.

**1. New researchers** — for each folder under `researchers/` (except `_template`) without a `profile/` folder: create the standard folder structure and run the `/add-researcher` pipeline from step 2 onward. If the researcher cannot be identified unambiguously, leave the template, note it in the status report, and skip to the next researcher.

**2. Inboxes** — for each existing researcher, run `profile-update`. Substantial changes flag the researcher for re-matching.

**3. Re-matching (flagged researchers only)** — run `horizon-matching` with the updated profile → `calls/[name]-calls-[YYYY-MM-DD].{md,pdf}`. If there are NEW top matches (≥ 14/20) outside the theme of the existing CORDIS analysis, run `cordis-analysis` once for the best new call's theme.

**4. Theme cache** — run `theme_cache.py --root themes list`. Refresh a **stale** theme (>60 days) only if at least one researcher in it was re-matched this week: regenerate that theme's `intelligence` and/or `cordis` artifact once, `store` it, and let the affected researchers `fetch` it. Never refresh more than two themes in one weekly run — the rest wait for the week they are actually needed.

**5. Reports (changed researchers only)** — run `html-report` (Type A) → `reports/[name]-briefing-[YYYY-MM-DD].html`. Today's date, never overwrite.

**6. Weekly status** in chat: new researchers created (with report links), updated profiles (files processed, new keywords, re-matched y/n), researchers with no news, new top calls across all researchers (id, title, deadline, best score), themes refreshed or reused, items awaiting user approval, next run date. Also generate the Type B weekly overview → `reports/weekly-status-[YYYY-MM-DD].html`.

## Rules

- Never send emails or external messages without explicit approval.
- Never modify a profile without a dated backup first.
- Unclassifiable inbox files → list under "Awaiting your review" in the status report.
- Reports regenerate only for researchers with changes.
