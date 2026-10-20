# Horizon Europe Consortium Finder
App that helps you identify and join a Horizon Europe consortium as a researcher

Delivered as a Claude plugin, `research-funding`. For a named researcher it builds a funding profile, matches open Horizon Europe calls, writes a Proposal Intelligence briefing, finds consortium partners in CORDIS, drafts work package lead pitch letters and combines everything in one HTML report.

## Install

**Claude Code** (type in the chat):

```
/plugin marketplace add madsberggreen/Horizon-Europe-Consortium-Finder
/plugin install research-funding@horizon-europe-consortium-finder
```

**Claude desktop app / Cowork** (paid plan required):

1. In Claude, open **Customize** in the left sidebar (in Cowork, open the **Cowork** tab first) and go to **Plugins**.
2. Click **Add** → **Add marketplace** → **Add from a repository**.
3. Enter `madsberggreen/Horizon-Europe-Consortium-Finder`.
4. Open the **Discover** tab and look for the plugin named **research-funding** (described as "Horizon Europe Consortium Finder"). It is listed among the plugins from Anthropic's own catalog, so search for `research-funding` if you don't see it. Select it and click **Install**.
5. Type `/start` in a new chat.

New versions arrive when you select **Check for updates** on the marketplace on the same **Plugins** page, or turn on **Sync automatically**.

**Can't find it?**
- Search for `research-funding`, not "Consortium Finder".
- Check that the marketplace was added: it should be listed on the **Plugins** page. If adding it failed, your organization may restrict which marketplaces you can add. Ask your Claude administrator, or install from a file (below).
- Select **Check for updates** on the marketplace, then look again.
- Cowork requires a paid plan (Pro, Max, Team or Enterprise).

**Alternative: install from a file.** Download `research-funding-<version>.plugin` from the latest release on the **Releases** page, then upload it under **Customize** → **Plugins**. To update, upload the new file.

If your organization restricts which marketplaces you may add, ask your Claude administrator to allow this repository or to add the plugin for everyone.

## Use

**Type `/start` in Claude.** A form appears in the chat. Choose **Simple search** (name, institution, optional ORCID iD; public data only) or **Advanced search** (adds your research idea and documents such as rejected applications or one-pagers), fill it in and press **Find me a consortium!**. Claude then generates the reports. In Advanced mode your input shapes the profile, the call matching, the policy briefing and the pitch letters. Documents are read in your browser and only reach Claude when you press the button.

In a regular chat, Claude gives you the reports as downloadable files at the end. In Cowork or Claude Code they are saved in your workspace folder.

You can also type commands directly in a workspace folder, for example:

- `/add-researcher Anne Jensen, <institution>` runs the full pipeline for one researcher.
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
