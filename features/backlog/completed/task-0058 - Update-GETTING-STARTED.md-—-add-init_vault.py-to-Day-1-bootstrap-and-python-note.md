---
id: TASK-0058
title: >-
  Update GETTING-STARTED.md — add init_vault.py to Day 1 bootstrap and python
  note
status: Done
assignee: []
created_date: '2026-05-28 16:06'
updated_date: '2026-05-28 16:56'
labels:
  - docs
  - portability
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - GETTING-STARTED.md
priority: medium
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two additions to GETTING-STARTED.md:

1. **init_vault.py bootstrap:** In the "Day 1: bootstrap" section of First week, mention `python3 init_vault.py` as the Windows-compatible alternative to `./init-vault.sh`.

2. **python note:** Add a short note: "On Windows, use `python` if `python3` is not recognised."
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Day 1 bootstrap section references `python3 init_vault.py` as the Windows path
- [ ] #2 A python3 vs python note is present, matched to the README wording
- [ ] #3 No other content changes
<!-- AC:END -->
