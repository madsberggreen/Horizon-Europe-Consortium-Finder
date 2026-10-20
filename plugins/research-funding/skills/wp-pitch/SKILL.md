---
name: wp-pitch
description: Generates a personalised outreach pitch positioning a researcher as a Work Package lead in a Horizon Europe consortium. Use when asked to write a pitch, draft a consortium contact letter, or prepare outreach to a potential coordinator.
---

# WP Lead Pitch

Drafts an outreach letter **from the researcher to a likely coordinator**, positioning them as a credible WP lead. This skill owns the letter format — other skills (html-report) render its output, they never re-specify it.

## Inputs (read in order, before drafting)

1. `profile/*.md` — portfolio, networks, ORCID
2. `calls/*.md` — the target call; copy expected outcomes **verbatim**
3. `cordis/*.md` — recipient organisation, their projects, "KEY CONTACTS — OUTREACH TARGETS"
4. `intelligence/*.md` — Key Documents / Impact-on-Policy entries touching this call

For each argument below, note the specific evidence + URL before writing prose. Missing evidence → address the gap honestly in the letter (Arguments 1/2/4) or omit (Argument 3). Never fabricate.

## Voice and format — non-negotiable

First person singular, from the researcher, signed by the researcher; name only in the sign-off. Professional, direct, ≤400 words body. English by default; Danish only if the **recipient** organisation is Danish. Every reference (project acronyms, COST codes, policy docs, topic ID) is a markdown link.

Structure: `Subject: [Topic ID] — exploring WP collaboration — [Name], [Institution]` → salutation (named contact from CORDIS Key Contacts if known, else "Dear [Organisation] Horizon Europe team,") → four arguments → low-friction close ("Would a 20-minute call in the week of [date] work? I can send a one-page concept note ahead" — or propose meeting at a near-term brokerage event from PI Section 5, linked) → sign-off with title, institution, ORCID link.

## The four arguments (in this order)

1. **Why I think you are interested in this call** (2–3 sentences). Cite ONE specific prior project of the recipient (acronym linked to CORDIS, one line on what they delivered) that signals interest in this topic. Named evidence, not flattery. E.g.: "Your coordination of [STRIDE](https://cordis.europa.eu/project/id/101132339) — particularly the stakeholder co-design work in WP3 — is exactly the groundwork [TOPIC-ID] asks partners to build on."
2. **Why I would be a good partner** (3–4 sentences). Quote ONE expected outcome **verbatim in quotation marks** (coordinators recognise their own call — never paraphrase). Name the method I bring + the track record proving I can run it, then one explicit mapping sentence: "This means I can take on a WP that turns [outcome phrase] into [deliverable type]."
3. **Network I can bring** (2–3 sentences — include only if real, otherwise omit; never pad). Active COST Action (linked, with role), current HEU/H2020 consortium (linked, plus the partner cluster I could bring), JU/ERIC/EIT-KIC seats, national coordination roles. Frame: "I'm adding a network slice, not one seat."
4. **Policy hook** (2–3 sentences). ONE Key Document or Impact entry from the PI report (named + linked): what the policy asks for in one phrase, and what my recent work concretely contributes. This turns "interested partner" into "partner with a policy story in hand".

## Verify and save

```bash
python "<skill-dir>/scripts/verify_pitch.py" letter.md TOPIC-ID outcomes.txt
```

Fix failures until clean (checks: first person, verbatim quote, no bare URLs, topic ID present, length). Save as `researchers/[Name]/pitches/[name]-pitch-[org-slug]-[YYYY-MM-DD].md` with header `# Pitch letter — [Name] → [Org]` / `_Call: [Topic ID] | Drafted: [date]_`.

Always present drafts for user review. Never send anything without explicit approval.
