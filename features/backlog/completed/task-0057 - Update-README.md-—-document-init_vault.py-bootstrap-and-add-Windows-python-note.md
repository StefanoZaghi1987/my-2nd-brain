---
id: TASK-0057
title: >-
  Update README.md — document init_vault.py bootstrap and add Windows python
  note
status: Done
assignee: []
created_date: '2026-05-28 16:06'
updated_date: '2026-05-28 16:54'
labels:
  - docs
  - portability
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - README.md
priority: medium
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two additions to README.md:

1. **init_vault.py bootstrap:** Add `python3 init_vault.py` as the Windows/universal path in the Quick start section, alongside the existing `./init-vault.sh` for Unix. Make clear that init-vault.sh remains the Unix path.

2. **Windows python note:** Add a one-sentence note under Dependencies: "On Windows, use `python` if `python3` is not recognised."
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Quick start section shows both `./init-vault.sh` (Unix) and `python3 init_vault.py` (universal/Windows)
- [ ] #2 Dependencies section contains a note: 'On Windows, use `python` if `python3` is not recognised.'
- [ ] #3 No other content changes
<!-- AC:END -->
