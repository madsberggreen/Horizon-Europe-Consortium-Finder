#!/usr/bin/env python3
"""Fetch OPEN/FORTHCOMING Horizon Europe calls from the EU Funding & Tenders API.

Usage:
    python fetch_calls.py --out calls_verified.json "keyword one" "keyword two" ...
    python fetch_calls.py --details TOPIC-ID [TOPIC-ID ...]    # full topic text incl. Expected Outcome

Prints a compact table (identifier | status | deadline | title) — summaries are
stored in the JSON only, so the chat context is not flooded. Read summaries
selectively for the calls you shortlist.

If the EU servers are blocked (Claude's sandbox often only allows GitHub and package
registries), both modes fall back to the repository's weekly GitHub mirror of all open
and forthcoming topics, with the same fields and the full topic descriptions.
"""
import argparse
import datetime as dt
import gzip
import html
import json
import os
import re
import sys
import time
import urllib.request

import requests

for _stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252 and crash on EU text
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

API_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
TOPIC_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails/{}.json"
MIRROR_BASE = os.environ.get(  # override only for testing
    "RF_MIRROR_BASE", "https://raw.githubusercontent.com/madsberggreen/Horizon-Europe-Consortium-Finder/data/")
MIRROR_URL = MIRROR_BASE + "calls/open-calls.json.gz"
MIRROR_MANIFEST = MIRROR_BASE + "manifest.json"
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
    """Live search. Returns (calls, reached) — reached is False when every request failed."""
    today = dt.date.today().isoformat()
    all_calls = {}  # keyed by topic identifier — deduplication built in
    reached = False
    for keyword in keywords:
        for page in (1, 2):  # 2 pages = up to 100 results per keyword
            try:
                results = search(keyword, page)
                reached = True
            except Exception as e:
                print(f"ERROR '{keyword}' p{page}: {e}", file=sys.stderr)
                if not reached:
                    break  # first request failed: the API is most likely blocked, don't hammer it
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
        if not reached:
            break
    return list(all_calls.values()), reached


_mirror = None


def load_mirror():
    """All open/forthcoming topics from the GitHub mirror, plus the date it was built."""
    global _mirror
    if _mirror is None:
        req = urllib.request.Request(MIRROR_URL, headers={"User-Agent": "horizon-europe-consortium-finder-plugin"})
        with urllib.request.urlopen(req, timeout=120) as r:
            topics = json.loads(gzip.decompress(r.read()).decode("utf-8"))
        built = "unknown"
        try:
            req = urllib.request.Request(MIRROR_MANIFEST, headers={"User-Agent": "horizon-europe-consortium-finder-plugin"})
            with urllib.request.urlopen(req, timeout=30) as r:
                built = json.load(r).get("built", "unknown")
        except Exception:
            pass
        _mirror = (topics, built)
    return _mirror


STOP = {"and", "of", "the", "for", "in", "on", "to", "a", "with"}


def stem(w):
    # Crude English normalisation so "textiles" matches "textile" and "studies" matches "study".
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def words(text):
    return {stem(w) for w in re.findall(r"[a-z0-9]+", str(text).lower()) if w not in STOP}


def fetch_from_mirror(keywords):
    """Local keyword search over the mirror, shaped like the live results."""
    topics, built = load_mirror()
    today = dt.date.today().isoformat()
    all_calls = {}
    for keyword in keywords:
        kw = words(keyword)
        if not kw:
            continue
        scored = []
        for t in topics:
            deadlines = t.get("deadlines") or []
            if deadlines and deadlines[-1] < today:
                continue
            title, tags, body = words(t["title"]), words(" ".join(t.get("keywords") or [])), words(t.get("description", ""))
            in_head = len(kw & (title | tags))
            in_body = len(kw & body)
            if in_head == 0 and in_body < len(kw):
                continue  # a single word buried in a long description is not a match
            scored.append((in_head * 3 + in_body, t))
        for _, t in sorted(scored, key=lambda x: -x[0])[:100]:
            if t["identifier"] in all_calls:
                continue
            deadlines = t.get("deadlines") or []
            all_calls[t["identifier"]] = {
                "identifier": t["identifier"],
                "call_identifier": t.get("call_identifier", ""),
                "title": t["title"],
                "status_label": t["status_label"],
                "deadline": next((d for d in deadlines if d >= today), deadlines[-1] if deadlines else ""),
                "opening_date": t.get("opening_date", ""),
                "budget_raw": t.get("budget_raw", ""),
                "type": t.get("type", ""),
                "url": t["url"],
                "summary": t.get("description", "")[:500],
                "matched_keyword": keyword,
            }
    return list(all_calls.values()), built


def details(ids):
    """Print each topic's full description (scope and Expected Outcome), live or from the mirror."""
    for ident in ids:
        text, source = "", ""
        try:
            r = requests.get(TOPIC_URL.format(ident.lower()), timeout=30)
            r.raise_for_status()
            raw = r.json().get("TopicDetails", {}).get("description", "")
            text = re.sub(r"\n{3,}", "\n\n", re.sub(r"<[^>]+>", "\n", raw))
            source = "EU Funding & Tenders Portal"
        except Exception:
            try:
                topics, built = load_mirror()
                t = next((t for t in topics if t["identifier"].lower() == ident.lower()), None)
                if t:
                    text, source = t.get("description", ""), f"GitHub mirror built {built}"
            except Exception as e:
                source = f"not available ({e})"
        print(f"===== {ident}  [source: {source or 'not found'}]")
        print(html.unescape(text).strip()[:12000] or "No description found for this identifier.")
        print()


def parse_budget(raw, ident):
    """This topic's own budget from the API's raw budget JSON.

    The JSON lists every topic of the parent call, so only the actions whose name starts
    with this topic's identifier count. Returns e.g. "EUR 20.0M (about 5 grants of EUR 3.5-4.0M)".
    """
    if not raw or raw in ("", "None", "[]", "{}"):
        return "See portal"
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return "See portal"
    total, grants, lo, hi = 0, 0, None, None
    seen = set()  # some topics repeat one shared budget for each action type (e.g. MSCA DN / DN-JD / DN-ID)
    for actions in (data.get("budgetTopicActionMap") or {}).values():
        for action in actions or []:
            name = str(action.get("action", "")).strip().upper()
            if not (name == ident.upper() or name.startswith(ident.upper() + " ")):
                continue
            shared = tuple(sorted((str(k), str(v)) for k, v in (action.get("budgetYearMap") or {}).items()))
            if shared in seen:
                continue
            seen.add(shared)
            for v in (action.get("budgetYearMap") or {}).values():
                try:
                    total += int(float(v))
                except Exception:
                    pass
            try:
                grants += int(action.get("expectedGrants") or 0)
            except Exception:
                pass
            for key, pick in (("minContribution", min), ("maxContribution", max)):
                try:
                    val = float(action.get(key) or 0)
                except Exception:
                    val = 0
                if val > 0:
                    if key == "minContribution":
                        lo = val if lo is None else pick(lo, val)
                    else:
                        hi = val if hi is None else pick(hi, val)
    if total <= 0:
        return "See portal"
    text = f"EUR {total/1_000_000:.1f}M"
    if grants and lo and hi:
        size = f"EUR {lo/1e6:.1f}M" if lo == hi else f"EUR {lo/1e6:.1f}-{hi/1e6:.1f}M"
        text += f" (about {grants} grant{'s' if grants != 1 else ''} of {size})"
    return text


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
    ap.add_argument("--details", action="store_true", help="Treat the arguments as topic IDs and print their full text")
    ap.add_argument("keywords", nargs="+")
    args = ap.parse_args()

    if args.details:
        details(args.keywords)
        return

    calls, reached = fetch(args.keywords)
    source = "EU Funding & Tenders API (live)"
    if not reached:
        print("The EU Funding & Tenders API is not reachable from here. Using the GitHub mirror ...", file=sys.stderr)
        try:
            calls, built = fetch_from_mirror(args.keywords)
            source = f"GitHub mirror of the EU Funding & Tenders API, built {built}"
        except Exception as e:
            print(f"ERROR: the GitHub mirror is not reachable either ({e}). No verified calls available.")
            sys.exit(1)
    for c in calls:
        c["budget"] = parse_budget(c.pop("budget_raw"), c["identifier"])
        c["cluster"] = cluster(c["identifier"])
    calls.sort(key=lambda c: (c["deadline"] or "9999"))

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(calls, f, indent=2, ensure_ascii=False)

    print(f"Verified OPEN/FORTHCOMING Horizon Europe calls: {len(calls)}  (saved to {args.out})")
    print(f"Source: {source}")
    print(f"{'IDENTIFIER':<50} {'STATUS':<12} {'DEADLINE':<11} TITLE")
    for c in calls:
        print(f"{c['identifier']:<50} {c['status_label']:<12} {c['deadline']:<11} {c['title'][:70]}")
    print("\nThese identifiers are the ONLY valid identifiers. Never use one that is not in this list.")


if __name__ == "__main__":
    main()
