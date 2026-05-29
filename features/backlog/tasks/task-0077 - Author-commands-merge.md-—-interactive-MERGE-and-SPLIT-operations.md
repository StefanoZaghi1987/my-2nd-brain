---
id: TASK-0077
title: Author commands/merge.md — interactive MERGE and SPLIT operations
status: To Do
assignee: []
created_date: '2026-05-29 11:45'
labels: []
milestone: m-2
dependencies:
  - TASK-0076
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - commands/merge.md
priority: high
ordinal: 5100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create `commands/merge.md` defining two inverse operations:

**MERGE** (two pages → one canonical): The user provides a source page (to be merged away) and a target page (canonical). The LLM shows a content diff, asks for confirmation and title, checks the backlink fanout via `find_backlinks.py`, gets the user to approve the merged content, writes it, rewrites all backlinks, deletes the source page, and updates `wiki/index.md` + `wiki/log.md`.

**SPLIT** (one page → two): Inverse. User marks which sections go to which new page. LLM writes both, rewrites backlinks per-section (asking when ambiguous), deletes the original, updates index + log.

Key guards (consistent with FORGET and Invariant #5):
- Fanout > 15 files: stop and report; require user to pick a subset or run multiple passes.
- Ask before deleting any prose.
- Never silently touch `shareable: true` views — warn instead.
- Not available in unattended mode.

References `.claude/skills/shared/find_backlinks.py` for backlink enumeration.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/merge.md defines the full MERGE protocol (steps matching the spec)
- [ ] #2 commands/merge.md defines the SPLIT protocol as an inverse operation
- [ ] #3 The >15 fanout guard is explicit: stop, report the list, do not proceed
- [ ] #4 shareable: true view handling is explicit: warn, do not modify
- [ ] #5 'Not available in unattended mode' is stated
- [ ] #6 The command references .claude/skills/shared/find_backlinks.py for backlink enumeration
- [ ] #7 The command notes updating wiki/index.md and wiki/log.md as final steps
<!-- AC:END -->
