# Data mirror (generated — do not edit)

This branch is rebuilt every Monday by the `Data mirror` GitHub Action from `tools/build_data_mirror.py` on `main`.

The research-funding plugin reads it when Claude's sandbox can't reach the EU servers directly:

- `calls/open-calls.json.gz` — all open and forthcoming Horizon Europe topics from the EU Funding & Tenders Portal, with their full descriptions
- `cordis/*.csv.gz` — the CORDIS Horizon Europe extracts from https://cordis.europa.eu/data/, trimmed to the columns the plugin uses
- `manifest.json` — build date and counts

Source data © European Union, reused under the Commission's reuse policy (Decision 2011/833/EU).
