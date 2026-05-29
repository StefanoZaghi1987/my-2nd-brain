---
id: TASK-0078
title: Add MERGE operation to CLAUDE.md (operations section + dispatch table)
status: Done
assignee: []
created_date: '2026-05-29 11:45'
updated_date: '2026-05-29 16:50'
labels: []
milestone: m-2
dependencies:
  - TASK-0077
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - CLAUDE.md
priority: medium
ordinal: 5200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add MERGE as the eleventh operation in `CLAUDE.md`, following the same structure as existing operations.

Three changes:
1. **Operations section**: add MERGE after REFRESH. Describe: what it does, the SPLIT inverse, the fanout guard, and that it is NOT available in unattended mode.
2. **Dispatch table**: add the row `MERGE | (LLM only) | find_backlinks.py` and update the heading from "Ten operations" to "Eleven operations".
3. **Unattended mode**: add an explicit note that MERGE is NOT available unattended (structural change — deletes pages and rewrites links).

Depends on task-0077 (commands/merge.md) for the protocol details.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CLAUDE.md has a MERGE section describing both MERGE and SPLIT
- [x] #2 Dispatch table includes MERGE row with find_backlinks.py as backing and heading says 'Eleven operations'
- [x] #3 Unattended mode CANNOT list includes MERGE (or a note that structural operations including MERGE are not available)
- [x] #4 CLAUDE.md operation count is consistent throughout (Eleven in heading, 11 rows in table, 11 sections)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
CLAUDE.md updated: heading changed to "Eleven operations", MERGE section added after REFRESH, dispatch table row added (MERGE | LLM only | find_backlinks.py), /merge and /split entries added to slash commands list, "merge or split pages" added to unattended CANNOT list, "merge" added to hot-cache "Written to" list. Commits: bad42e7, 958e3d9.
<!-- SECTION:FINAL_SUMMARY:END -->
