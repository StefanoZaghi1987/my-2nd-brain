---
id: TASK-0054
title: Update commands/fetch.md and commands/refresh.md to use python3
status: Done
assignee: []
created_date: '2026-05-28 16:06'
updated_date: '2026-05-28 16:49'
labels:
  - docs
  - portability
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - commands/fetch.md
  - commands/refresh.md
priority: low
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Both command files contain bash code blocks that invoke the inbox fetcher script with `python`. On Linux, `python` may be Python 2 or absent. The canonical command on Linux/macOS is `python3`.

commands/fetch.md: one code block with `python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py`
commands/refresh.md: one code block with `python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py`

Both should use `python3`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/fetch.md bash code blocks use `python3` (not `python`)
- [ ] #2 commands/refresh.md bash code blocks use `python3` (not `python`)
- [ ] #3 No other content in either file changes
<!-- AC:END -->
