#!/usr/bin/env python3
"""Download the official CORDIS Horizon Europe bulk files into the workspace.

The CORDIS data is public (EU Open Data, cordis.europa.eu/data) and too large to
ship inside the plugin, so every workspace fetches its own copy on first use and
refreshes it when it gets old. CORDIS republishes the extracts roughly monthly.

Usage:
    python download_cordis.py --data-dir "<workspace>/cordis-data" [--max-age 30] [--force]

Exit codes: 0 = data ready (fresh or just downloaded), 1 = download failed and no
usable local copy exists. If a download fails but an older copy exists, the old copy
is kept, a warning is printed and the exit code is 0.
"""
import argparse
import datetime as dt
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BASE_URL = "https://cordis.europa.eu/data/"
ZIPS = [
    "cordis-HORIZONprojects-csv.zip",             # project, organization, topics, policyPriorities, euroSciVoc, ...
    "cordis-HORIZONprojectDeliverables-csv.zip",  # projectDeliverables
    "cordis-HORIZONprojectPublications-csv.zip",  # projectPublications
    "cordis-HORIZONreports-csv.zip",              # reportSummaries
]
REQUIRED = ["project.csv", "organization.csv", "topics.csv", "policyPriorities.csv",
            "projectDeliverables.csv", "projectPublications.csv"]
STAMP = "SOURCE.txt"


def downloaded_on(data_dir):
    stamp = data_dir / STAMP
    if not stamp.exists():
        return None
    for line in stamp.read_text(encoding="utf-8").splitlines():
        if line.startswith("downloaded:"):
            try:
                return dt.date.fromisoformat(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def has_required(data_dir):
    # Older workspaces may hold the main files under their pre-2026 names.
    alt = {"project.csv": "cordis-HORIZONprojects.csv",
           "organization.csv": "cordis-HORIZONorganizations.csv"}
    return all((data_dir / f).exists() or (data_dir / alt.get(f, f)).exists() for f in REQUIRED)


def download_all(data_dir):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name in ZIPS:
            print(f"Downloading {name} ...", flush=True)
            target = tmp / name
            with urllib.request.urlopen(BASE_URL + name, timeout=300) as r, open(target, "wb") as f:
                shutil.copyfileobj(r, f)
            with zipfile.ZipFile(target) as z:
                for member in z.namelist():
                    if member.endswith(".csv") and "/" not in member:
                        z.extract(member, tmp / "csv")
        data_dir.mkdir(parents=True, exist_ok=True)
        for csv in (tmp / "csv").iterdir():
            shutil.move(str(csv), data_dir / csv.name)
    (data_dir / STAMP).write_text(
        f"source: {BASE_URL} (official CORDIS Horizon Europe bulk extracts)\n"
        f"downloaded: {dt.date.today().isoformat()}\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--max-age", type=int, default=30, help="Refresh when older than this many days")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    data_dir = Path(args.data_dir).expanduser().resolve()

    when = downloaded_on(data_dir)
    present = has_required(data_dir)
    if present and not args.force:
        if when and (dt.date.today() - when).days <= args.max_age:
            print(f"CORDIS data is fresh (downloaded {when}). Nothing to do.")
            return 0
        if when is None:
            print("CORDIS data present but download date unknown — refreshing.")

    try:
        download_all(data_dir)
    except Exception as e:  # network blocked, portal down, disk full ...
        if present:
            print(f"WARNING: refresh failed ({e}). Using existing local copy"
                  + (f" from {when}." if when else "."))
            return 0
        print(f"ERROR: could not download CORDIS data ({e}).")
        return 1

    if not has_required(data_dir):
        print("ERROR: download finished but expected files are missing: "
              + ", ".join(f for f in REQUIRED if not (data_dir / f).exists()))
        return 1
    print(f"CORDIS data ready in {data_dir} (downloaded {dt.date.today()}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
