---
id: TASK-0062
title: Fix adopt_drop.py example path in inbox-fetcher SKILL.md
status: Done
assignee: []
created_date: '2026-05-29 11:42'
updated_date: '2026-05-29 15:03'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - skills/inbox-fetcher/SKILL.md
priority: medium
ordinal: 1100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Same root cause as the /ingest command path bug: `skills/inbox-fetcher/SKILL.md` lines 164-166 show manual-run examples using bare `skills/inbox-fetcher/scripts/adopt_drop.py`. In a deployed vault the script lives under `.claude/skills/…`, so these examples would fail if a user copied them verbatim.

All `fetch_inbox.py` examples in the same file already use the correct `.claude/skills/…` prefix — this task brings the `adopt_drop.py` examples into line with them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 SKILL.md lines 164-166 example invocations use `.claude/skills/inbox-fetcher/scripts/adopt_drop.py`
- [x] #2 All script example paths in inbox-fetcher/SKILL.md consistently use the `.claude/skills/…` prefix
<!-- AC:END -->



## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Fixed three adopt_drop.py bare paths in SKILL.md lines 164-166. All path references now consistently use .claude/skills/... Commit 1b87a4b.
<!-- SECTION:FINAL_SUMMARY:END -->
