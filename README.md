# Horizon-Europe-Networking
App that helps you identify and join a Horizon Europe consortium as a researcher

Delivered as a Claude plugin, `research-funding`. For a named researcher it builds a funding profile, matches open Horizon Europe calls, writes a Proposal Intelligence briefing, finds consortium partners in CORDIS, drafts work package lead pitch letters and combines everything in one HTML report.

## Install

**Claude Code** (type in the chat):

```
/plugin marketplace add madsberggreen/Horizon-Europe-Networking
/plugin install research-funding@horizon-europe-networking
```

**Claude desktop app / Cowork** (paid plan required):

1. Download `research-funding-<version>.plugin` from the latest release on this repository's **Releases** page.
2. In Claude, open **Customize** in the left sidebar (in Cowork, open the **Cowork** tab first) and go to **Plugins**.
3. Upload the downloaded file. Plugins added this way are saved on your computer.
4. Type `/start` in a new chat.

To update, download the new file from Releases and upload it again.

Adding this repository as a marketplace (**Plugins** → **Add** → **Add marketplace** → **Add from a repository** → `madsberggreen/Horizon-Europe-Networking`) only works reliably for public repositories. This repository is private, so use the file instead.

The repository is private. Colleagues need read access on GitHub (Settings → Collaborators) to download the file or install via Claude Code.

## Use

**Easiest: type `/start` in Claude.** A form appears in the chat. Choose simple or advanced search, fill it in and press **Find me a consortium!**. The pipeline starts straight away.

**Alternative: the start page.** Open https://claude.ai/artifact/R1rkx8dabe6gKRKpYNZ43E, choose **Simple search** (name, institution, optional ORCID; public data only) or **Advanced search** (adds your research idea and documents such as rejected applications or one-pagers), click **Copy request** and paste it into Claude. In Advanced mode your input shapes the profile, the call matching, the policy briefing and the pitch letters. Documents are read in your browser and only reach Claude when you paste the request. The page's source is `app/index.html`.

You can also type commands directly in a workspace folder, for example:

- `/add-researcher Anne Jensen, VIA University College` runs the full pipeline for one researcher.
- `/update-profiles` runs the full pipeline for every new folder you have created under `researchers/`. Existing researchers are left untouched.

Nothing runs automatically: a report is only generated when you ask for it.

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
