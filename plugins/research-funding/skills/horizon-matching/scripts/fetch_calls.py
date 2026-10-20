#!/usr/bin/env python3
"""Fetch live OPEN/FORTHCOMING Horizon Europe calls from the EU Funding & Tenders API.

Usage:
    python fetch_calls.py --out calls_verified.json "keyword one" "keyword two" ...

Prints a compact table (identifier | status | deadline | title) — summaries are
stored in the JSON only, so the chat context is not flooded. Read summaries
selectively for the calls you shortlist.
"""
import argparse
import json
import sys
import time

import requests

API_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
HEADERS = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
# OPEN=31094502, FORTHCOMING=31094501, CLOSED=31094503 (never include)
ALLOWED = {"31094502": "OPEN", "31094501": "FORTHCOMING"}


def fetch(keywords):
    all_calls = {}  # keyed by identifier — deduplication built in
    for keyword in keywords:
        for page in (1, 2):  # 2 pages = up to 100 results per keyword
            encoded = requests.utils.quote(keyword)
            data = (f"apiKey=SEDIA&text={encoded}&pageSize=50&pageNumber={page}"
                    f"&sortBy=relevance&programmePeriod=2021+-+2027")
            try:
                resp = requests.post(API_URL, headers=HEADERS, data=data, timeout=30)
                results = resp.json().get("results", [])
            except Exception as e:
                print(f"ERROR '{keyword}' p{page}: {e}", file=sys.stderr)
                continue
            for item in results:
                m = item.get("metadata", {})
                raw_status = (m.get("status") or m.get("sortStatus") or [""])[0]
                if raw_status not in ALLOWED:
                    continue  # discard CLOSED and everything else
                prog = (m.get("programmePeriod") or [""])[0]
                if "2021" not in prog:
                    continue  # discard non-Horizon Europe
                ident = (m.get("callIdentifier") or m.get("topicIdentifier") or [""])[0]
                if not ident or ident in all_calls:
                    continue
                # Always build the topic URL deterministically — never trust the API's URL field.
                topic_url = ("https://ec.europa.eu/info/funding-tenders/opportunities/portal/"
                             f"screen/opportunities/topic-details/{ident}")
                all_calls[ident] = {
                    "identifier": ident,
                    "title": item.get("title") or (m.get("topicTitle") or [""])[0]
                             or (m.get("callTitle") or [""])[0] or "",
                    "status_label": ALLOWED[raw_status],
                    "deadline": (m.get("deadlineDate") or [""])[0][:10],
                    "opening_date": (m.get("startDate") or m.get("openingDate") or [""])[0][:10],
                    "budget_raw": str((m.get("budget") or m.get("budgetOverview") or [""])[0]),
                    "type": (m.get("typeOfAction") or [""])[0],
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
