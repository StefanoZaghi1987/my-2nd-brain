---
id: TASK-0046
title: Rename ingests_since_last_lint to fetches_since_last_lint in vault_state.py
status: Done
assignee: []
created_date: '2026-05-28 16:05'
updated_date: '2026-05-28 16:25'
labels:
  - bug-fix
  - rename
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - skills/shared/vault_state.py
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The counter `ingests_since_last_lint` in vault_state.py `_DEFAULTS` is incremented by fetch_inbox.py on a successful FETCH, not on INGEST. INGEST is LLM-only and has no Python hook. The name is a semantic lie. Rename both the state key and the config key to accurately reflect what they measure.

No behavior change — purely a rename. Existing `.lint/state.yaml` files have the old key; after rename the counter resets to 0 (one missed auto-lint trigger at most — acceptable, no migration script needed).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 In `_DEFAULTS["lint"]`, `"auto_trigger_after_ingests": 5` is renamed to `"auto_trigger_after_fetches": 5`
- [ ] #2 No other logic in `vault_state.py` changes
- [ ] #3 `pytest tests/test_vault_state.py` passes (after tests are updated in a separate task)
<!-- AC:END -->
