---
name: profile-update
description: Scans a researcher's inbox folder for new files and updates their structured profile. Use when new documents have been added for a researcher, or when asked to update a profile.
---

# Profile Update

Processes new files in a researcher's `inbox/` and updates their profile. Runs only when the user asks, for one researcher at a time.

## Execute

1. **Detect** — list `inbox/` files, compare timestamps against the last-processed entry in `inbox/inbox-log.md`. No new files → log "No new content — skipped", stop.
2. **Classify** each new file: Project idea | Draft application | CV or bio | Publication/preprint | Context note | Other (flag for manual review). Log: `| [date] | [file] | [class] | New | Pending |`.
3. **Extract** by class — ideas/notes: research questions, methods, keywords, named calls; drafts: objectives, WP structure, partner wishes, contradictions with existing profile (flag); CV: career stage, affiliation, grants; publications: title, venue, keywords, co-author institutions.
4. **Update profile** — backup `profile/[name]-profile.md` as `profile/[name]-profile-backup-[YYYY-MM-DD].md` first. Update THEMATIC FOCUS, KEYWORDS (respect the keyword quality gate in researcher-profiling), COLLABORATION HISTORY, GAPS AND OPPORTUNITIES, CAREER STAGE. Mark changed sections `[Updated YYYY-MM-DD]`.
5. **Flag downstream** — material change to focus/keywords → tell the user that a new call-matching run and report may be worthwhile; minor (one new publication) → log only.
6. **Log** — update `inbox-log.md` (`Processed` + note).

Never trigger call-matching or a new report yourself; the user decides.
