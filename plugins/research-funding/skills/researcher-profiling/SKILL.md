---
name: researcher-profiling
description: Builds a structured funding profile for a researcher at any institution. Use when adding a new researcher, when asked to "profile" or "find info on" a researcher, or when a researcher name and institution are mentioned in the context of Horizon Europe funding.
---

# Researcher Profiling

Builds a structured researcher interest profile from local project files plus ORCID/UCviden (Pure) publication data. Always the first step before matching against funding opportunities.

## Mode

- **Simple** (default) — public sources only. Skip step 1. Put `_Sources: publicly available data only_` under the profile title.
- **Advanced** — also read the newest `inbox/user-input-*.md`. The user may want to move into a field that differs from their track record, so the profile must describe both where they have been and where they want to go:
  - Add an **INTENDED DIRECTION (from user input)** section after THEMATIC FOCUS: the idea in 3–5 sentences, what is new compared with the track record, and which existing strengths carry over.
  - KEYWORDS: 4–6 of the 10–15 keywords must come from the idea, marked `(idea)`, ranked among the top 8 so call-matching does not drown them in the track record.
  - GAPS AND OPPORTUNITIES: name the bridge between the track record and the idea, and the competences a consortium partner would need to supply.
  - From rejected applications: list the weaknesses the evaluators named under GAPS AND OPPORTUNITIES as "to strengthen". Never copy evaluator wording into any other output.
  - Put `_Sources: public data + user input ([file names])_` under the profile title.

## Execute

1. **Local files** (Advanced mode only) — scan the researcher's folder: previous applications (research questions, methods, keywords, impact), preliminary findings/working papers (core claims, disciplines, empirical focus), CVs/bios (career stage, affiliation, collaborators).
2. **External data** — query ORCID (last 10 years: titles, journals, keywords, co-author institutions); supplement with UCviden by name + institution if available. If no unambiguous match is found, stop and ask the user for ORCID/department rather than guessing.
3. **Synthesise** into this structure:

```
RESEARCHER PROFILE
==================
Name / Institution / ORCID

THEMATIC FOCUS
- Primary research areas (max 5, specific terms not broad disciplines)
- Methodological strengths (e.g. RCT, ethnography, computational modelling)
- Empirical domains (geography, population, sector)

KEYWORDS FOR FUNDING SEARCH
[10–15, ranked by centrality]

COLLABORATION HISTORY
- Key co-author institutions | previous EU projects (grant numbers) | cross-disciplinary links

GAPS AND OPPORTUNITIES
- Topics the researcher is moving toward | underexploited methodological capacity

CAREER STAGE CONTEXT
[Early / Mid / Senior — relevant for ERC vs. collaborative targeting]
```

**Keyword quality gate (this caps everything downstream):** keywords must be fundable-topic phrases as they would appear in a call text ("circular bioeconomy side-streams", "teacher-AI complementarity"), never discipline labels ("biology", "education"). Include 2–3 policy-adjacent terms (mission/cluster vocabulary). One keyword per distinct research area.

## Output

Save as `researchers/[Name]/profile/[name]-profile.md`. Confirm with the user before proceeding to the next pipeline step (unless running inside /add-researcher, which never pauses).
