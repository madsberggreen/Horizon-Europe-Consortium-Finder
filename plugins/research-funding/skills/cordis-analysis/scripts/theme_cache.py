#!/usr/bin/env python3
"""Theme-level cache for Proposal Intelligence and CORDIS artifacts.

Both are landscape descriptions of a THEME, not of a person: the policy
documents, COST Actions, DGs, brokerage events and the set of organisations
that win in an area are identical for two researchers in the same subtheme.
This script stores them once per theme and hands them back until they go stale
(default 60 days). Researcher-specific judgement — strategic assessment, WP
role, geographic argument, pitch letters — is NEVER cached.

Layout:
    themes/_taxonomy.json          canonical subtheme list (edit via `new`)
    themes/<slug>/intelligence-YYYY-MM-DD.{md,json}
    themes/<slug>/cordis-YYYY-MM-DD.{md,json}

Commands:
    resolve  "kw" "kw" ... [--cluster HORIZON-CL6]   which theme + is it fresh?
    status   <slug>                                  freshness per artifact kind
    list                                             all themes at a glance
    new      --slug s --label L --clusters C [--keywords ...] [--researchers ...]
    store    --slug s --kind intelligence --file F [--date YYYY-MM-DD]
    fetch    --slug s --kind cordis --researcher "Name" --out PATH

`fetch` writes a provenance banner into the copy so nobody mistakes a reused
landscape for fresh research.

Exit codes for `resolve`: 0 = fresh cache hit, 3 = theme known but stale/missing,
4 = no confident theme match (generate fresh and consider `new`).
"""
import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

KINDS = ("intelligence", "cordis")
DEFAULT_TTL = 60
STOP = {"and", "of", "the", "for", "in", "on", "to", "with", "a", "eu", "european"}


def today():
    return dt.date.today()


def root_dir(args):
    return Path(args.root).expanduser().resolve()


def load_tax(root):
    f = root / "_taxonomy.json"
    if not f.exists():
        # First run in a new workspace: no themes cached yet.
        return {"ttl_days": DEFAULT_TTL, "themes": []}
    return json.loads(f.read_text(encoding="utf-8"))


def save_tax(root, tax):
    (root / "_taxonomy.json").write_text(
        json.dumps(tax, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tokens(text):
    return {t for t in re.split(r"[^a-z0-9]+", str(text).lower()) if t and t not in STOP and len(t) > 2}


def score_theme(theme, kws, cluster):
    """Fraction of query keywords that land in this theme, plus a cluster bonus.

    A multi-word keyword needs at least two shared tokens (or an exact phrase
    match) to count — otherwise 'digital media literacy' would hit every theme
    that merely mentions 'digital'.
    """
    phrases, bag = set(), set()
    for field in ("keywords", "aliases", "label"):
        v = theme.get(field, [])
        for item in ([v] if isinstance(v, str) else v):
            phrases.add(" ".join(sorted(tokens(item))))
            bag |= tokens(item)
    if not kws:
        return 0.0, []

    def hit(k):
        kt = tokens(k)
        if not kt:
            return False
        if " ".join(sorted(kt)) in phrases:
            return True
        shared = kt & bag
        return len(shared) >= (1 if len(kt) == 1 else 2)

    hits = [k for k in kws if hit(k)]
    s = len(hits) / len(kws)
    if cluster and any(cluster.upper().startswith(c.upper()) or c.upper().startswith(cluster.upper())
                       for c in theme.get("clusters", [])):
        s += 0.15
    return round(min(s, 1.0), 3), hits


def artifacts(root, slug, kind):
    d = root / slug
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob(f"{kind}-*.md")):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
        if m:
            out.append((dt.date.fromisoformat(m.group(1)), p))
    return sorted(out, reverse=True)


def freshness(root, slug, kind, ttl):
    a = artifacts(root, slug, kind)
    if not a:
        return "MISSING", None, None
    date, path = a[0]
    age = (today() - date).days
    return ("FRESH" if age <= ttl else "STALE"), age, path


def cmd_resolve(args):
    root = root_dir(args)
    tax = load_tax(root)
    ttl = args.ttl or tax.get("ttl_days", DEFAULT_TTL)
    ranked = []
    for t in tax["themes"]:
        s, hits = score_theme(t, args.keywords, args.cluster)
        ranked.append((s, hits, t))
    ranked.sort(key=lambda x: -x[0])

    print(f"Query: {len(args.keywords)} keywords"
          + (f" | cluster {args.cluster}" if args.cluster else ""))
    print(f"TTL: {ttl} days\n")
    print(f"{'score':>6}  {'slug':<38} matched keywords")
    for s, hits, t in ranked[:5]:
        print(f"{s:>6.2f}  {t['slug']:<38} {', '.join(hits[:6]) or '—'}")

    if not ranked:
        print("\nNO MATCH — theme cache is empty. Generate fresh, then `new` + `store`.")
        sys.exit(4)
    best_s, best_hits, best = ranked[0]
    if best_s < args.threshold:
        print(f"\nNO CONFIDENT MATCH (best {best_s:.2f} < {args.threshold}).")
        print("→ Generate fresh, then register the new subtheme with `theme_cache.py new`.")
        return 4

    print(f"\nTHEME: {best['slug']}  ({best['label']})")
    stale_or_missing = False
    for kind in KINDS:
        state, age, path = freshness(root, best["slug"], kind, ttl)
        detail = f"{age} days old — {path.name}" if path else "no cached artifact"
        print(f"  {kind:<13} {state:<8} {detail}")
        if state != "FRESH":
            stale_or_missing = True

    if stale_or_missing:
        print("\n→ Generate the missing/stale kind(s) fresh, then `store` them.")
        return 3
    print("\n→ REUSE: run `fetch` for each kind instead of researching again.")
    return 0


def cmd_status(args):
    root = root_dir(args)
    tax = load_tax(root)
    ttl = args.ttl or tax.get("ttl_days", DEFAULT_TTL)
    theme = next((t for t in tax["themes"] if t["slug"] == args.slug), None)
    if not theme:
        sys.exit(f"Unknown theme: {args.slug}")
    print(f"{theme['slug']} — {theme['label']}")
    print(f"  clusters:    {', '.join(theme.get('clusters', []))}")
    print(f"  researchers: {', '.join(theme.get('researchers', [])) or '—'}")
    for kind in KINDS:
        state, age, path = freshness(root, args.slug, kind, ttl)
        print(f"  {kind:<13} {state:<8} {(str(age) + ' days — ' + path.name) if path else '—'}")
    return 0


def cmd_list(args):
    root = root_dir(args)
    tax = load_tax(root)
    ttl = args.ttl or tax.get("ttl_days", DEFAULT_TTL)
    print(f"{'slug':<38} {'intel':<12} {'cordis':<12} researchers")
    for t in tax["themes"]:
        cells = []
        for kind in KINDS:
            state, age, _ = freshness(root, t["slug"], kind, ttl)
            cells.append(state if state == "MISSING" else f"{state} ({age}d)")
        print(f"{t['slug']:<38} {cells[0]:<12} {cells[1]:<12} {len(t.get('researchers', []))}")
    return 0


def cmd_new(args):
    root = root_dir(args)
    root.mkdir(parents=True, exist_ok=True)
    tax = (json.loads((root / "_taxonomy.json").read_text(encoding="utf-8"))
           if (root / "_taxonomy.json").exists() else {"ttl_days": DEFAULT_TTL, "themes": []})
    if any(t["slug"] == args.slug for t in tax["themes"]):
        sys.exit(f"Theme already exists: {args.slug}")
    tax["themes"].append({
        "slug": args.slug, "label": args.label,
        "clusters": args.clusters or [], "keywords": args.keywords or [],
        "aliases": args.aliases or [], "researchers": args.researchers or [],
    })
    tax["themes"].sort(key=lambda t: t["slug"])
    save_tax(root, tax)
    (root / args.slug).mkdir(exist_ok=True)
    print(f"Registered theme {args.slug} → {root / args.slug}")
    return 0


def cmd_store(args):
    root = root_dir(args)
    tax = load_tax(root)
    theme = next((t for t in tax["themes"] if t["slug"] == args.slug), None)
    if not theme:
        sys.exit(f"Unknown theme: {args.slug} — register it with `new` first.")
    src = Path(args.file)
    if not src.exists():
        sys.exit(f"No such file: {src}")
    date = args.date or today().isoformat()
    dest_dir = root / args.slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{args.kind}-{date}{src.suffix}"
    shutil.copy2(src, dest)
    print(f"Stored: {dest}")
    if args.researcher and args.researcher not in theme.get("researchers", []):
        theme.setdefault("researchers", []).append(args.researcher)
        save_tax(root, tax)
        print(f"Linked researcher {args.researcher} to {args.slug}")
    return 0


BANNER = (
    "> **Reused from the theme cache.** This landscape analysis covers the shared subtheme "
    "*{label}* (`{slug}`) and was generated {date} ({age} days ago). It is identical for every "
    "researcher in this subtheme — the researcher-specific assessment, role recommendation and "
    "pitch letters are produced fresh and are not part of this cache. Regenerate the theme if the "
    "policy landscape has shifted.\n\n"
)


def cmd_fetch(args):
    root = root_dir(args)
    tax = load_tax(root)
    theme = next((t for t in tax["themes"] if t["slug"] == args.slug), None)
    if not theme:
        sys.exit(f"Unknown theme: {args.slug}")
    ttl = args.ttl or tax.get("ttl_days", DEFAULT_TTL)
    state, age, path = freshness(root, args.slug, args.kind, ttl)
    if path is None:
        sys.exit(f"No cached {args.kind} artifact for {args.slug}.")
    if state == "STALE" and not args.allow_stale:
        sys.exit(f"Cached {args.kind} is {age} days old (TTL {ttl}). "
                 f"Regenerate, or pass --allow-stale deliberately.")
    date = re.search(r"(\d{4}-\d{2}-\d{2})", path.name).group(1)
    body = path.read_text(encoding="utf-8")
    banner = BANNER.format(label=theme["label"], slug=theme["slug"], date=date, age=age)
    lines = body.split("\n")
    if lines and lines[0].startswith("# "):          # keep the H1 on top
        out_text = lines[0] + "\n\n" + banner + "\n".join(lines[1:]).lstrip("\n")
    else:
        out_text = banner + body
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(out_text, encoding="utf-8")
    print(f"Fetched {args.kind} for theme {args.slug} ({age} days old) → {out}")

    sidecar = path.with_suffix(".json")
    if sidecar.exists():
        shutil.copy2(sidecar, out.with_suffix(".json"))
        print(f"  + data sidecar → {out.with_suffix('.json')}")
    if args.researcher and args.researcher not in theme.get("researchers", []):
        theme.setdefault("researchers", []).append(args.researcher)
        save_tax(root, tax)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default="themes", help="themes directory (default: ./themes)")
    p.add_argument("--ttl", type=int, help=f"freshness window in days (default {DEFAULT_TTL})")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("resolve"); r.add_argument("keywords", nargs="+")
    r.add_argument("--cluster"); r.add_argument("--threshold", type=float, default=0.25)
    r.set_defaults(fn=cmd_resolve)

    s = sub.add_parser("status"); s.add_argument("slug"); s.set_defaults(fn=cmd_status)
    sub.add_parser("list").set_defaults(fn=cmd_list)

    n = sub.add_parser("new")
    n.add_argument("--slug", required=True); n.add_argument("--label", required=True)
    n.add_argument("--clusters", nargs="*"); n.add_argument("--keywords", nargs="*")
    n.add_argument("--aliases", nargs="*"); n.add_argument("--researchers", nargs="*")
    n.set_defaults(fn=cmd_new)

    st = sub.add_parser("store")
    st.add_argument("--slug", required=True); st.add_argument("--kind", required=True, choices=KINDS)
    st.add_argument("--file", required=True); st.add_argument("--date"); st.add_argument("--researcher")
    st.set_defaults(fn=cmd_store)

    f = sub.add_parser("fetch")
    f.add_argument("--slug", required=True); f.add_argument("--kind", required=True, choices=KINDS)
    f.add_argument("--out", required=True); f.add_argument("--researcher")
    f.add_argument("--allow-stale", action="store_true")
    f.set_defaults(fn=cmd_fetch)

    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
