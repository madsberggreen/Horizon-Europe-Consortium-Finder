#!/usr/bin/env python3
"""Shared link verifier for all pipeline outputs (markdown or HTML).

Rule: every identifier and reference must be a clickable link — never plain text,
never a bare URL. If a URL cannot be found for an entry, the entry is omitted upstream.

Canonical URL patterns:
    Topic:   https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{TOPIC-ID}
    CORDIS:  https://cordis.europa.eu/project/id/{PROJECT-ID}
    COST:    https://www.cost.eu/actions/{CAxxxxx}/

Usage:
    python verify_links.py file.md          # or file.html
Exit code 0 = pass; non-zero = failures printed to stdout. Fix and re-run until clean.
"""
import re
import sys


def verify(text: str, kind: str) -> list:
    failures = []
    if kind == "html":
        stripped = re.sub(r'(?:href|src)="[^"]*"', "", text)
        def unlinked(token):
            return re.search(rf"(?<!>)\b{re.escape(token)}\b(?![^<]*</a>)", text)
    else:  # markdown
        stripped = re.sub(r"\[[^\]]*\]\([^)]*\)", "", text)
        def unlinked(token):
            return token in stripped

    # 1. No bare URLs in visible text
    bare = re.findall(r'https?://[^\s<>"\')\]]+', stripped)
    if bare:
        failures.append(f"Bare URLs in visible text: {bare[:5]}")
    # 2. Every HORIZON-* topic ID must be inside a link
    for tid in set(re.findall(r"\bHORIZON-[A-Z0-9]+(?:-[A-Z0-9]+)+\b", text)):
        if unlinked(tid):
            failures.append(f"Topic ID not linked: {tid}")
    # 3. Every COST Action code must be inside a link
    for code in set(re.findall(r"\bCA\d{5}\b", text)):
        if unlinked(code):
            failures.append(f"COST Action not linked: {code}")
    return failures


def main():
    path = sys.argv[1]
    text = open(path, encoding="utf-8").read()
    kind = "html" if path.lower().endswith((".html", ".htm")) else "md"
    failures = verify(text, kind)
    if failures:
        print(f"LINK VERIFICATION FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print(f"Link verification passed: {path}")


if __name__ == "__main__":
    main()
