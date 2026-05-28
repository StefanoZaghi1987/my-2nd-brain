---
id: TASK-0047
title: >-
  Rename ingests_since_last_lint to fetches_since_last_lint in fetch_inbox.py
  and lint.py
status: Done
assignee: []
created_date: '2026-05-28 16:05'
updated_date: '2026-05-28 16:30'
labels:
  - bug-fix
  - rename
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - skills/inbox-fetcher/scripts/fetch_inbox.py
  - skills/vault-linter/scripts/lint.py
priority: medium
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In `process_vault()`, fetch_inbox.py reads and writes the state key `ingests_since_last_lint`. This task renames that key to `fetches_since_last_lint` to match the rename in vault_state.py `_DEFAULTS`.

Context: the counter tracks successful fetches (HTML + PDF), not ingests. The rename corrects the semantics without changing any behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 In `process_vault()`, the `read_state()` call reads key `"fetches_since_last_lint"` (not `"ingests_since_last_lint"`)
- [ ] #2 The `write_state()` call writes key `"fetches_since_last_lint"`
- [ ] #3 pytest tests/test_fetch_inbox.py passes
- [ ] #4 #3 In lint.py's final _write_state(...) call, the key "fetches_since_last_lint": 0 is renamed to "fetches_since_last_lint": 0
<!-- AC:END -->
