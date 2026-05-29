---
id: TASK-0061
title: >-
  Fix adopt_drop.py path in commands/ingest.md (breaks /ingest in deployed
  vaults)
status: To Do
assignee: []
created_date: '2026-05-29 11:42'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - commands/ingest.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In a deployed vault, `init_vault.py` installs all scripts under `.claude/skills/…`. The `/ingest` command at `commands/ingest.md:23` calls `adopt_drop.py` with a bare `skills/inbox-fetcher/scripts/adopt_drop.py` path — this path does not exist post-install, so the drop-zone pre-flight silently fails every time `/ingest` is run.

The fix is a one-line path correction in the command file.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/ingest.md line 23 invokes `.claude/skills/inbox-fetcher/scripts/adopt_drop.py` (not bare `skills/…`)
- [ ] #2 Every other adopt_drop.py invocation in commands/ uses the same `.claude/skills/…` prefix
- [ ] #3 Grep for `skills/inbox-fetcher/scripts/adopt_drop` in commands/ returns zero bare-path matches
<!-- AC:END -->
