#!/usr/bin/env python3
"""Verify a pitch letter before delivery.

Usage:
    python verify_pitch.py letter.md TOPIC-ID outcomes.txt
        outcomes.txt = the call's expected outcomes, verbatim (one or more lines)

Checks: first-person voice, verbatim outcome quote, no bare URLs, topic ID present,
length <= ~400 words body. Exit 0 = pass.
"""
import re
import sys


def verify(letter: str, topic_id: str, expected_outcomes: list) -> list:
    failures = []
    third = re.findall(r"\b(the researcher|Dr\.? \w+ (?:is|has|brings))", letter, flags=re.I)
    if third:
        failures.append(f"Third-person phrasing: {third[:3]} — rewrite in first person")
    quoted = [q.strip().lower() for q in re.findall(r'[""\"]([^""\"]+)[""\"]', letter) if len(q.strip()) > 15]
    eo = " ".join(expected_outcomes).lower()
    if not any(q in eo for q in quoted):
        failures.append("No verbatim quote from the call's expected outcomes found (Argument 2)")
    stripped = re.sub(r"\[[^\]]*\]\([^)]*\)", "", letter)
    bare = re.findall(r"https?://[^\s)>\]]+", stripped)
    if bare:
        failures.append(f"Bare URLs not in markdown link form: {bare[:3]}")
    if topic_id and topic_id not in letter:
        failures.append(f"Topic ID {topic_id} not referenced")
    words = len(re.findall(r"\b\w+\b", letter))
    if words > 500:
        failures.append(f"Letter is {words} words — trim body to <= 400")
    return failures


if __name__ == "__main__":
    letter = open(sys.argv[1], encoding="utf-8").read()
    topic_id = sys.argv[2] if len(sys.argv) > 2 else ""
    outcomes = open(sys.argv[3], encoding="utf-8").read().splitlines() if len(sys.argv) > 3 else []
    failures = verify(letter, topic_id, outcomes)
    if failures:
        print("PITCH VERIFICATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("Pitch verification passed.")
