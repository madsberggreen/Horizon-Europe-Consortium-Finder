#!/usr/bin/env python3
"""Fetch live OPEN/FORTHCOMING Horizon Europe calls from the EU Funding & Tenders API.

Usage:
    python fetch_calls.py --out calls_verified.json "keyword one" "keyword two" ...

Prints a compact table (identifier | status | deadline | title) — summaries are
stored in the JSON only, so the chat context is not flooded. Read summaries
selectively for the calls you shortlist.
"""
import argparse
import datetime as dt
import json
import sys
import time

import requests

API_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
# OPEN=31094502, FORTHCOMING=31094501, CLOSED=31094503 (never include)
ALLOWED = {"31094502": "OPEN", "31094501": "FORTHCOMING"}
HORIZON_EUROPE = "43108390"  # frameworkProgramme id of Horizon Europe
# The same filter the Funding & Tenders portal sends. Without it the search returns
# organisations, news and closed calls, and the open topics drown in them.
QUERY = {"bool": {"must": [
    {"terms": {"type": ["1"]}},                     # calls for proposals (topics)
    {"terms": {"status": list(ALLOWED)}},           # open + forthcoming only
    {"term": {"programmePeriod": "2021 - 2027"}},
    {"terms": {"frameworkProgramme": [HORIZON_EUROPE]}},
]}}


def first(m, *keys):
    for k in keys:
        v = m.get(k)
        if v:
            return v[0] if isinstance(v, list) else v
    return ""


def search(keyword, page):
    files = {"query": ("blob", json.dumps(QUERY), "application/json"),
             "languages": ("blob", json.dumps(["en"]), "application/json")}
    params = {"apiKey": "SEDIA", "text": keyword, "pageSize": 50, "pageNumber": page}
    resp = requests.post(API_URL, params=params, files=files, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def fetch(keywords):
    today = dt.date.today().isoformat()
    all_calls = {}  # keyed by topic identifier — deduplication built in
    for keyword in keywords:
        for page in (1, 2):  # 2 pages = up to 100 results per keyword
            try:
                results = search(keyword, page)
            except Exception as e:
                print(f"ERROR '{keyword}' p{page}: {e}", file=sys.stderr)
                continue
            for item in results:
                m = item.get("metadata", {})
                raw_status = first(m, "status", "sortStatus")
                if raw_status not in ALLOWED:
                    continue  # discard CLOSED and everything else
                if first(m, "frameworkProgramme") != HORIZON_EUROPE:
                    continue  # discard non-Horizon Europe
                ident = first(m, "identifier")  # the topic, not the call it belongs to
                if not ident or ident in all_calls:
                    continue
                # Multi-stage topics list several deadlines; the last one decides whether it is still live.
                deadlines = sorted(d[:10] for d in (m.get("deadlineDate") or []) if d)
                if deadlines and deadlines[-1] < today:
                    continue  # portal still says OPEN/FORTHCOMING, but every deadline has passed
                # Always build the topic URL deterministically — never trust the API's URL field.
                topic_url = ("https://ec.europa.eu/info/funding-tenders/opportunities/portal/"
                             f"screen/opportunities/topic-details/{ident}")
                all_calls[ident] = {
                    "identifier": ident,
                    "call_identifier": first(m, "callIdentifier"),
                    "title": first(m, "title") or item.get("title") or item.get("summary") or "",
                    "status_label": ALLOWED[raw_status],
                    "deadline": next((d for d in deadlines if d >= today), deadlines[-1] if deadlines else ""),
                    "opening_date": first(m, "startDate", "openingDate")[:10],
                    "budget_raw": str(first(m, "budgetOverview", "budget")),
                    "type": first(m, "typesOfAction", "typeOfAction"),
                    "url": topic_url,
                    "summary": (item.get("summary") or item.get("content") or "")[:500],
                    "matched_keyword": keyword,
                }
            time.sleep(0.3)
    return list(all_calls.values())


def parse_budget(raw):
    """Human-readable budget from the API's raw budget JSON."""
    if not raw or raw in ("", "None", "[]"):
        return "See portal"
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return "See portal"
    total = 0
    for actions in data.get("budgetTopicActionMap", {}).values():
        for action in actions:
            for v in action.get("budgetYearMap", {}).values():
                try:
                    total += int(v)
                except Exception:
                    pass
    return f"EUR {total/1_000_000:.1f}M" if total > 0 else "See portal"


CLUSTER_PREFIXES = [
    ("HORIZON-MISS", "Missions"), ("HORIZON-CL2", "Cluster 2 (Culture, Creativity, Society)"),
    ("HORIZON-CL3", "Cluster 3 (Civil Security)"), ("HORIZON-CL4", "Cluster 4 (Digital, Industry, Space)"),
    ("HORIZON-CL5", "Cluster 5 (Climate, Energy, Mobility)"),
    ("HORIZON-CL6", "Cluster 6 (Food, Bioeconomy, Environment)"),
    ("HORIZON-CL1", "Cluster 1 (Health)"), ("HORIZON-NEB", "New European Bauhaus"),
    ("HORIZON-EIE", "Innovation Ecosystems"), ("HORIZON-ERC", "ERC"),
    ("HORIZON-MSCA", "MSCA"), ("HORIZON-WIDERA", "Widening/ERA"), ("HORIZON-INFRA", "Research Infrastructures"),
]


def cluster(ident):
    for prefix, name in CLUSTER_PREFIXES:
        if ident.startswith(prefix):
            return name
    return "Other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="calls_verified.json")
    ap.add_argument("keywords", nargs="+")
    args = ap.parse_args()

    calls = fetch(args.keywords)
    for c in calls:
        c["budget"] = parse_budget(c.pop("budget_raw"))
        c["cluster"] = cluster(c["identifier"])
    calls.sort(key=lambda c: (c["deadline"] or "9999"))

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(calls, f, indent=2, ensure_ascii=False)

    print(f"Verified OPEN/FORTHCOMING Horizon Europe calls: {len(calls)}  (saved to {args.out})")
    print(f"{'IDENTIFIER':<50} {'STATUS':<12} {'DEADLINE':<11} TITLE")
    for c in calls:
        print(f"{c['identifier']:<50} {c['status_label']:<12} {c['deadline']:<11} {c['title'][:70]}")
    print("\nThese identifiers are the ONLY valid identifiers. Never use one that is not in this list.")


if __name__ == "__main__":
    main()
