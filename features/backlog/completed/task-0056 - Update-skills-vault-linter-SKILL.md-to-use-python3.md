---
id: TASK-0056
title: Update skills/vault-linter/SKILL.md to use python3
status: Done
assignee: []
created_date: '2026-05-28 16:06'
updated_date: '2026-05-28 16:52'
labels:
  - docs
  - portability
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - skills/vault-linter/SKILL.md
priority: low
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
skills/vault-linter/SKILL.md contains bash code blocks that invoke lint.py with `python`. Normalise to `python3` for consistency with the canonical command on Linux/macOS.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All bash code blocks in vault-linter/SKILL.md use `python3` (not `python`)
- [ ] #2 No other content changes
- [ ] #3 #2 Lines 51, 54, 57: `python` → `python3`
<!-- AC:END -->
