---
name: researcher-profiling
description: Builds a structured funding profile for a researcher at any institution. Use when adding a new researcher, when asked to "profile" or "find info on" a researcher, or when a researcher name and institution are mentioned in the context of Horizon Europe funding.
---

# Researcher Profiling

Builds a structured researcher interest profile from local project files plus ORCID/UCviden (Pure) publication data. Always the first step before matching against funding opportunities.

## Execute

1. **Local files** — scan the researcher's folder: previous applications (research questions, methods, keywords, impact), preliminary findings/working papers (core claims, disciplines, empirical focus), CVs/bios (career stage, affiliation, collaborators).
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
