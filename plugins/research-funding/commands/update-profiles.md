---
description: Find new researcher folders in the workspace and run the full onboarding pipeline for each of them
---

# /update-profiles

Run only when the user asks. Finds researcher folders that have not been processed yet and runs the onboarding pipeline for each. It does not touch researchers that already have a profile — no inbox processing, re-matching or report regeneration. Runs autonomously — no mid-run confirmations.

## Phases

**0. CORDIS data check** — run `python "${CLAUDE_PLUGIN_ROOT}/skills/cordis-analysis/scripts/download_cordis.py" --data-dir "<workspace>/cordis-data"` (the script sits in the `cordis-analysis` skill's `scripts/` folder). It refreshes the CORDIS extracts when older than 30 days and otherwise does nothing.

**1. New researchers** — for each folder under `researchers/` (except `_template`) without a `profile/` folder: create the standard folder structure and run the `/add-researcher` pipeline from step 2 onward. If the researcher cannot be identified unambiguously, leave the template, note it in the status message, and skip to the next researcher.

**Status message** in chat: new researchers processed (with report links), researchers skipped and why, and the CORDIS download date (from `cordis-data/SOURCE.txt`).

## Rules

- Never send emails or external messages without explicit approval.
- Never modify an existing researcher's files.
