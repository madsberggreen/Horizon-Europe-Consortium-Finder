#!/usr/bin/env python3
"""CORDIS consortium analysis — deterministic data layer.

Runs the full join sequence over the local CORDIS bulk files and computes the five
analytical dimensions (relevance ratio, budget weighting, EU experience, geographic
gap, Matthew effect). Claude interprets the output; this script never guesses.

Usage:
    python analyse_cordis.py --data-dir "<workspace>/cordis-data" \
        --out cordis_analysis.json \
        [--topic-code HORIZON-CL6-2025-...] [--country DK] \
        "keyword 1" "keyword 2" ...

Selection: projects matching --topic-code (via topics.csv, prefix match) OR any
keyword (case-insensitive, in objective/title/keywords). Prints a compact summary;
full detail goes to the JSON.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

import sys
for _stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252 and crash on EU text
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# download_cordis.py stores the official file names; older workspaces used renamed copies.
ALT_NAMES = {"cordis-HORIZONprojects.csv": "project.csv",
             "cordis-HORIZONorganizations.csv": "organization.csv"}


MIN_PARTNERS = 3     # a "consortium" has at least this many partners
MIN_CONSORTIA = 20   # below this, country shares in a theme are noise
UNDER_RATIO = 0.75   # theme share below 75% of the country's overall share = underrepresented


def read(data_dir, name):
    path = Path(data_dir) / name
    if not path.exists() and name in ALT_NAMES:
        path = Path(data_dir) / ALT_NAMES[name]
    return pd.read_csv(path, sep=";", quotechar='"', dtype=str,
                       on_bad_lines="skip", low_memory=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", default="cordis_analysis.json")
    ap.add_argument("--topic-code", default=None)
    ap.add_argument("--country", default="DK", help="Researcher's country code")
    ap.add_argument("--top-orgs", type=int, default=12)
    ap.add_argument("keywords", nargs="*")
    args = ap.parse_args()

    proj = read(args.data_dir, "cordis-HORIZONprojects.csv")
    orgs = read(args.data_dir, "cordis-HORIZONorganizations.csv")
    topics = read(args.data_dir, "topics.csv")

    # --- Select the relevant project set ---
    mask = pd.Series(False, index=proj.index)
    if args.topic_code:
        ids = set(topics[topics["topic"].str.startswith(args.topic_code, na=False)]["projectID"])
        mask |= proj["id"].isin(ids)
    if args.keywords:
        blob = (proj["objective"].fillna("") + " " + proj["title"].fillna("")
                + " " + proj.get("keywords", pd.Series("", index=proj.index)).fillna("")).str.lower()
        for kw in args.keywords:
            mask |= blob.str.contains(kw.lower(), regex=False)
    sel = proj[mask].copy()
    sel_ids = set(sel["id"])
    if not len(sel):
        print("No matching projects — broaden keywords or drop the topic code.")
        return

    o = orgs[orgs["projectID"].isin(sel_ids)].copy()
    o["ecContribution"] = pd.to_numeric(o["ecContribution"], errors="coerce").fillna(0)

    # --- Org-level dimensions ---
    total_projects_per_org = orgs.groupby("name")["projectID"].nunique()  # EU experience (all topics)
    g = o.groupby("name").agg(
        country=("country", "first"),
        projects_in_topic=("projectID", "nunique"),
        ec_in_topic=("ecContribution", "sum"),
        coordinator_in_topic=("role", lambda r: int((r == "coordinator").sum())),
        activity=("activityType", "first"),
        org_url=("organizationURL", "first"),
        org_id=("organisationID", "first"),
    ).reset_index()
    g["total_heu_projects"] = g["name"].map(total_projects_per_org).fillna(0).astype(int)
    g["relevance_ratio"] = (g["projects_in_topic"] / g["total_heu_projects"].clip(lower=1)).round(3)
    g["power_broker"] = g["total_heu_projects"] >= 100
    g["score"] = (g["projects_in_topic"] * 2 + g["coordinator_in_topic"] * 3
                  + g["ec_in_topic"] / 1_000_000)
    top = g.sort_values("score", ascending=False).head(args.top_orgs)
    top = top.fillna({"country": "", "activity": "", "org_url": "", "org_id": ""})

    # --- Geographic gap ---
    # Counted over real consortia only (3+ partners): almost half of all Horizon Europe projects
    # have a single beneficiary (ERC, MSCA fellowships) and would drag every country's share down.
    # A country is "underrepresented" when its share in this theme is clearly below its share of
    # ALL Horizon Europe consortia - a fixed threshold would flag every small country.
    n_proj = len(sel_ids)
    home = args.country.upper()
    partners = orgs.groupby("projectID")["name"].nunique()
    consortia_all = set(partners[partners >= MIN_PARTNERS].index)
    consortia_theme = sel_ids & consortia_all
    n_cons = len(consortia_theme)

    def share(project_ids, country=None):
        sub = orgs[orgs["projectID"].isin(project_ids)]
        if country:
            return 100.0 * sub[sub["country"] == country]["projectID"].nunique() / max(len(project_ids), 1)
        return (sub.groupby("country")["projectID"].nunique().sort_values(ascending=False)
                / max(len(project_ids), 1) * 100).round(1)

    country_pct = share(consortia_theme)
    home_pct = round(share(consortia_theme, home), 1)
    home_base = round(share(consortia_all, home), 1)
    home_ratio = round(home_pct / home_base, 2) if home_base else None
    enough = n_cons >= MIN_CONSORTIA
    under = bool(enough and home_ratio is not None and home_ratio < UNDER_RATIO)
    if not enough:
        geo_verdict = (f"too few consortia in this theme ({n_cons}) to judge - "
                       "do not use a geographic-balance argument")
    elif under:
        geo_verdict = ("UNDERREPRESENTED in this theme compared with its usual share - "
                       "the geographic-balance argument can be used, quoting both numbers")
    else:
        geo_verdict = "not underrepresented - do NOT use a geographic-balance argument"

    # --- Policy flags ---
    policy = {}
    try:
        pp = read(args.data_dir, "policyPriorities.csv")
        pps = pp[pp["projectID"].isin(sel_ids)]
        for col in ("ai", "biodiversity", "cleanAir", "climate", "digitalAgenda"):
            if col in pps.columns:
                vals = pd.to_numeric(pps[col], errors="coerce").fillna(0)
                policy[col] = round(float((vals > 0).mean() * 100), 1)
    except FileNotFoundError:
        pass

    # --- Deliverable type patterns ---
    deliv_types, deliv_noncoord = {}, {}
    try:
        dv = read(args.data_dir, "projectDeliverables.csv")
        dvs = dv[dv["projectID"].isin(sel_ids)]
        deliv_types = dvs["deliverableType"].value_counts().head(6).to_dict()
    except FileNotFoundError:
        pass

    # --- Warm-lead candidates from publications ---
    warm = []
    try:
        pub = read(args.data_dir, "projectPublications.csv")
        pubs = pub[pub["projectID"].isin(sel_ids)].fillna("")  # empty cells are NaN, which `or ""` doesn't catch
        for _, r in pubs.head(200).iterrows():
            warm.append({"authors": (r.get("authors") or "")[:200],
                         "project": r.get("projectAcronym"), "projectID": r.get("projectID"),
                         "doi": r.get("doi"), "title": (r.get("title") or "")[:150]})
    except FileNotFoundError:
        pass

    result = {
        "selection": {"keywords": args.keywords, "topic_code": args.topic_code,
                      "projects_matched": n_proj},
        "top_organisations": [
            {"name": r["name"], "country": r["country"],
             "projects_in_topic": int(r["projects_in_topic"]),
             "coordinator_in_topic": int(r["coordinator_in_topic"]),
             "ec_in_topic_eur": int(r["ec_in_topic"]),
             "total_heu_projects": int(r["total_heu_projects"]),
             "relevance_ratio": float(r["relevance_ratio"]),
             "power_broker": bool(r["power_broker"]),
             "activity_type": r["activity"], "org_url": r["org_url"],
             "cordis_org_url": f"https://cordis.europa.eu/search?q=%27{r['org_id']}%27" if r["org_id"] else None}
            for _, r in top.iterrows()],
        "sample_projects": [
            {"id": r["id"], "acronym": r["acronym"], "title": (r["title"] or "")[:120],
             "topic": r["topics"], "ec_contribution": r["ecMaxContribution"],
             "start": r["startDate"], "end": r["endDate"],
             "url": f"https://cordis.europa.eu/project/id/{r['id']}"}
            for _, r in sel.sort_values("ecMaxContribution", key=lambda s: pd.to_numeric(s, errors="coerce"),
                                        ascending=False).head(15).fillna("").iterrows()],
        "geography": {"basis": f"consortia with {MIN_PARTNERS}+ partners",
                      "consortia_in_theme": n_cons,
                      "top_countries_pct": country_pct.head(10).to_dict(),
                      "home_country": home, "home_country_pct": home_pct,
                      "home_country_pct_all_heu_consortia": home_base,
                      "home_ratio_theme_vs_all": home_ratio,
                      "home_underrepresented": under,
                      "verdict": geo_verdict},
        "policy_flags_pct": policy,
        "deliverable_types": deliv_types,
        "publication_leads": warm[:40],
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # --- Compact console summary ---
    print(f"Projects matched: {n_proj}  (detail in {args.out})")
    print(f"\nTOP ORGANISATIONS (by combined score):")
    for r in result["top_organisations"]:
        pb = " [POWER BROKER]" if r["power_broker"] else ""
        print(f"  {r['name'][:55]:<55} {r['country']:<3} in-topic:{r['projects_in_topic']:>3} "
              f"coord:{r['coordinator_in_topic']:>2} EC:€{r['ec_in_topic_eur']/1e6:>6.1f}M "
              f"rel:{r['relevance_ratio']:.2f} total:{r['total_heu_projects']}{pb}")
    print(f"\nGEOGRAPHY: top {', '.join(f'{k} {v}%' for k, v in list(result['geography']['top_countries_pct'].items())[:5])}")
    print(f"  (share of the {n_cons} consortia with {MIN_PARTNERS}+ partners in this theme)")
    print(f"  {home}: in {home_pct}% of consortia in this theme vs {home_base}% of all Horizon Europe consortia "
          f"-> {geo_verdict}")
    if policy:
        print(f"POLICY FLAGS: {', '.join(f'{k} {v}%' for k, v in sorted(policy.items(), key=lambda x: -x[1]))}")
    if deliv_types:
        print(f"DELIVERABLE TYPES: {', '.join(f'{k} ({v})' for k, v in deliv_types.items())}")


if __name__ == "__main__":
    main()
