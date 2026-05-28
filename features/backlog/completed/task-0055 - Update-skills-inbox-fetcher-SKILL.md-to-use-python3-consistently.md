---
id: TASK-0055
title: Update skills/inbox-fetcher/SKILL.md to use python3 consistently
status: Done
assignee: []
created_date: '2026-05-28 16:06'
updated_date: '2026-05-28 16:51'
labels:
  - docs
  - portability
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - skills/inbox-fetcher/SKILL.md
priority: low
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
skills/inbox-fetcher/SKILL.md uses `python` in some code blocks and `python3` in others — inconsistent within the same file. Normalise all shell invocations to `python3` to match the canonical command on Linux/macOS.

Occurrences to update are in the "How to run it" section and any other bash code blocks in the file.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All bash code blocks in SKILL.md use `python3` (not `python`)
- [ ] #2 No other content changes
<!-- AC:END -->
