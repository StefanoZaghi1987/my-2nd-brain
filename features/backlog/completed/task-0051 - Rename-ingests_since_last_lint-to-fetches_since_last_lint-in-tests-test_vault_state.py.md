---
id: TASK-0051
title: >-
  Rename ingests_since_last_lint to fetches_since_last_lint in
  tests/test_vault_state.py
status: Done
assignee: []
created_date: '2026-05-28 16:05'
updated_date: '2026-05-28 16:43'
labels:
  - bug-fix
  - rename
  - tests
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - tests/test_vault_state.py
priority: medium
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
tests/test_vault_state.py contains multiple test methods that write and assert the state key `ingests_since_last_lint`. All occurrences must be renamed to `fetches_since_last_lint` to match the renamed key in vault_state.py.

Occurrences appear in: TestReadState.test_parses_existing_state_file, TestWriteState.test_creates_file_and_lint_dir_when_absent, TestWriteState.test_patches_existing_key, TestWriteState.test_preserves_keys_not_in_updates, TestWriteState.test_adds_new_key_to_existing_file.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All string literals `"ingests_since_last_lint"` replaced with `"fetches_since_last_lint"`
- [ ] #2 pytest tests/test_vault_state.py passes with no failures or errors
<!-- AC:END -->
