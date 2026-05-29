---
id: TASK-0074
title: Add .review/ state and report templates; update init_vault.py and .gitignore
status: To Do
assignee: []
created_date: '2026-05-29 11:44'
labels: []
milestone: m-1
dependencies:
  - TASK-0072
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - init_vault.py
priority: medium
ordinal: 3200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The REVIEW operation needs its own state directory, mirroring the `.lint/` pattern. Three changes:

1. **`init_vault.py`**: create `.review/` directory with `.gitkeep` during bootstrap; write a stub `.review/state.yaml` with initial values:
   ```yaml
   last_review: null
   scope: null
   findings_count: 0
   last_exit_code: 0
   ```

2. **`.gitignore` template in `init_vault.py`**: add `.review/` alongside `.lint/` so generated vaults don't commit review reports.

3. **State schema**: document the `.review/state.yaml` schema fields (`last_review`, `scope`, `findings_count`, `last_exit_code`) inline as YAML comments in the stub.

Also register `review.md` in the `COMMANDS` list in `init_vault.py` so it is installed into every vault bootstrapped after this change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 init_vault.py creates .review/ directory during bootstrap
- [ ] #2 init_vault.py writes a .review/state.yaml stub with the four fields and inline comments
- [ ] #3 .gitignore template in init_vault.py includes .review/ alongside .lint/
- [ ] #4 'review.md' appears in the COMMANDS list in init_vault.py
- [ ] #5 Running python init_vault.py <tmp> produces a vault with .review/ and state.yaml present
<!-- AC:END -->
