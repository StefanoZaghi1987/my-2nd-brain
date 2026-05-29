---
id: TASK-0074
title: Add .review/ state and report templates; update init_vault.py and .gitignore
status: To Do
assignee: []
created_date: '2026-05-29 11:44'
updated_date: '2026-05-29 12:04'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Key implementation details for a fresh agent:

**Function name**: the helper in init_vault.py is `_write_if_absent` (with underscore prefix), not `write_if_absent`. It takes `(path, content, label)` and is called at lines ~218-223.

**Write function**: the function that calls `_write_if_absent` is `write_base_files()` (line 208), not `create_base_files`.

**Gitignore note**: the `_GITIGNORE` constant in init_vault.py (line 169) does NOT currently include `.lint/`. When adding `.review/`, also add `.lint/` alongside it. Append to the end of `_GITIGNORE` before the closing triple-quote.

**DIRS list**: `.lint` is at line 72. Add `.review` in the same list to ensure the directory is created during bootstrap.

**COMMANDS list** (line 86): currently `["save", "view", "reflect", "forget", "lint", "promote", "refresh", "ingest", "fetch", "hot", "playwright-fetch"]`. Add `"review"` here.

**Shared scripts block** (lines 340-348): currently copies only `vault_state.py`. Extend to a loop over a list to also copy `review_scope.py`.
<!-- SECTION:NOTES:END -->
