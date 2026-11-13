#!/usr/bin/env python3
"""Build the data mirror that the plugin falls back to when Claude's sandbox can't reach EU servers.

Claude's code-execution sandbox only allows package registries and GitHub by default, so
api.tech.ec.europa.eu and cordis.europa.eu are often blocked for users. This script runs on
GitHub Actions (weekly), fetches the same data from the EU, trims it to what the plugin uses,
and writes gzip files that the workflow publishes on the repository's `data` branch, where
raw.githubusercontent.com serves them.

Usage:
    python tools/build_data_mirror.py --out mirror

Output:
    mirror/manifest.json                built date + counts
    mirror/calls/open-calls.json.gz     every OPEN/FORTHCOMING Horizon Europe topic with full description
    mirror/cordis/<name>.csv.gz         trimmed CORDIS extracts (same file names and columns the scripts read)
"""
import argparse
import csv
import datetime as dt
import gzip
import html
import io
import json
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import requests

for _stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252 and crash on EU text
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
TOPIC_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails/{}.json"
PORTAL_TOPIC = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{}"
STATUS = {"31094502": "OPEN", "31094501": "FORTHCOMING"}
HORIZON_EUROPE = "43108390"
QUERY = {"bool": {"must": [
    {"terms": {"type": ["1"]}},
    {"terms": {"status": list(STATUS)}},
    {"term": {"programmePeriod": "2021 - 2027"}},
    {"terms": {"frameworkProgramme": [HORIZON_EUROPE]}},
]}}

CORDIS_URL = "https://cordis.europa.eu/data/"
CORDIS_ZIPS = ["cordis-HORIZONprojects-csv.zip", "cordis-HORIZONprojectDeliverables-csv.zip",
               "cordis-HORIZONprojectPublications-csv.zip"]
# Only the columns analyse_cordis.py reads.
CORDIS_KEEP = {
    "project.csv": ["id", "acronym", "status", "title", "startDate", "endDate", "totalCost",
                    "ecMaxContribution", "topics", "frameworkProgramme", "fundingScheme",
                    "objective", "keywords"],
    "organization.csv": ["projectID", "projectAcronym", "organisationID", "name", "shortName",
                         "activityType", "country", "organizationURL", "role", "ecContribution"],
    "topics.csv": ["projectID", "topic", "title"],
    "policyPriorities.csv": None,  # small; keep every column
    "projectDeliverables.csv": ["projectID", "deliverableType"],
    "projectPublications.csv": ["projectID", "projectAcronym", "authors", "title", "doi"],
}


def first(m, *keys):
    for k in keys:
        v = m.get(k)
        if v:
            return v[0] if isinstance(v, list) else v
    return ""


def plain_text(raw):
    text = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>", "\n", raw or "")
    text = re.sub(r"(?i)<li[^>]*>", "- ", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()


def build_calls(out):
    today = dt.date.today().isoformat()
    topics, page = {}, 1
    while True:
        # A fixed sort is required: unsorted paging repeats some topics and silently skips others.
        files = {"query": ("blob", json.dumps(QUERY), "application/json"),
                 "languages": ("blob", json.dumps(["en"]), "application/json"),
                 "sort": ("blob", json.dumps({"field": "identifier", "order": "ASC"}), "application/json")}
        r = requests.post(SEARCH_URL, params={"apiKey": "SEDIA", "text": "***", "pageSize": 100,
                                              "pageNumber": page}, files=files, timeout=60)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            break
        for item in results:
            m = item.get("metadata", {})
            ident = first(m, "identifier")
            status = first(m, "status", "sortStatus")
            if not ident or status not in STATUS or first(m, "frameworkProgramme") != HORIZON_EUROPE:
                continue
            deadlines = sorted(d[:10] for d in (m.get("deadlineDate") or []) if d)
            if deadlines and deadlines[-1] < today:
                continue
            topics[ident] = {
                "identifier": ident,
                "call_identifier": first(m, "callIdentifier"),
                "title": first(m, "title") or item.get("summary") or "",
                "status_label": STATUS[status],
                "deadlines": deadlines,
                "opening_date": first(m, "startDate")[:10],
                "type": first(m, "typesOfAction", "typeOfAction"),
                "keywords": m.get("keywords") or [],
                "url": PORTAL_TOPIC.format(ident),
            }
        page += 1
        time.sleep(0.3)
    print(f"Topics: {len(topics)} open/forthcoming with a future deadline", flush=True)

    for i, ident in enumerate(sorted(topics), 1):
        t = topics[ident]
        try:
            d = requests.get(TOPIC_URL.format(ident.lower()), timeout=30)
            d.raise_for_status()
            td = d.json().get("TopicDetails", {})
            t["description"] = plain_text(td.get("description", ""))[:15000]
            t["budget_raw"] = json.dumps(td.get("budgetOverviewJSONItem") or {})
        except Exception as e:
            print(f"  details failed for {ident}: {e}", file=sys.stderr)
            t["description"], t["budget_raw"] = "", ""
        if i % 100 == 0:
            print(f"  details {i}/{len(topics)}", flush=True)
        time.sleep(0.15)

    path = out / "calls" / "open-calls.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(sorted(topics.values(), key=lambda t: t["identifier"]), f, ensure_ascii=False)
    return len(topics)


def build_cordis(out):
    counts = {}
    target = out / "cordis"
    target.mkdir(parents=True, exist_ok=True)
    for name in CORDIS_ZIPS:
        print(f"Downloading {name}", flush=True)
        with urllib.request.urlopen(CORDIS_URL + name, timeout=600) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
        for member in z.namelist():
            if member not in CORDIS_KEEP:
                continue
            keep = CORDIS_KEEP[member]
            text = io.TextIOWrapper(z.open(member), encoding="utf-8", newline="")
            reader = csv.DictReader(text, delimiter=";", quotechar='"')
            cols = keep or reader.fieldnames
            rows = 0
            with gzip.open(target / f"{member}.gz", "wt", encoding="utf-8", newline="") as f:
                w = csv.writer(f, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)
                w.writerow(cols)
                for row in reader:
                    w.writerow([row.get(c, "") for c in cols])
                    rows += 1
            counts[member] = rows
            print(f"  {member}: {rows} rows", flush=True)
    missing = set(CORDIS_KEEP) - set(counts)
    if missing:
        raise SystemExit(f"CORDIS extracts missing: {sorted(missing)}")
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="mirror")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    csv.field_size_limit(sys.maxsize if sys.maxsize < 2**31 else 2**31 - 1)
    n_calls = build_calls(out)
    cordis = build_cordis(out)
    manifest = {"built": dt.date.today().isoformat(), "calls": n_calls, "cordis_rows": cordis,
                "sources": {"calls": SEARCH_URL, "cordis": CORDIS_URL}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
