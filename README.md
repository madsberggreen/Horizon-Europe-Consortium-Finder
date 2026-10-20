# Horizon-Europe-Networking
App that helps you identify and join a Horizon Europe consortium as a researcher

Delivered as a Claude plugin, `research-funding`. For a named researcher it builds a funding profile, matches open Horizon Europe calls, writes a Proposal Intelligence briefing, finds consortium partners in CORDIS, drafts work package lead pitch letters and combines everything in one HTML report.

## Install

**Claude Code** (type in the chat):

```
/plugin marketplace add madsberggreen/Horizon-Europe-Networking
/plugin install research-funding@horizon-europe-networking
```

**Claude desktop app / Cowork:** add this GitHub repository as a plugin marketplace under plugin settings, then install `research-funding`.

The repository is private. Colleagues need read access on GitHub (Settings → Collaborators) to install it.

## Use

Open a folder to work in (your workspace) and type, for example:

- `/add-researcher Anne Jensen, VIA University College` runs the full pipeline for one researcher.
- `/update-profiles` processes new files in every researcher's `inbox/` folder and updates their reports.

Everything is saved in the workspace:

```
researchers/<Name>/   profile, calls, intelligence, cordis, pitches, reports
themes/               shared cache of theme landscapes (reused for 60 days)
cordis-data/          CORDIS bulk data, downloaded automatically
```

## CORDIS data

The partner analysis uses the official CORDIS Horizon Europe extracts (https://cordis.europa.eu/data/). You do not need to download them yourself: the pipeline checks `cordis-data/` every time it starts, downloads the data on first use (about 55 MB) and refreshes it when it is more than 30 days old. The download date is in `cordis-data/SOURCE.txt`.

The workspace needs internet access to `cordis.europa.eu`. Without it, the CORDIS step falls back to web search and says so in the report.

## Requirements

Python 3 with `pandas` (CORDIS analysis), `requests` (call matching) and `reportlab` (PDFs). If one is missing, ask Claude to install it (`pip install pandas requests reportlab`).

## Privacy

Researcher data (CVs, profiles, reports) stays in each user's own workspace and is never part of this repository.
