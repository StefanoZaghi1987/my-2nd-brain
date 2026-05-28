---
id: TASK-0002
title: Create skills/shared/vault_state.py shared state utility
status: Done
assignee: []
created_date: '2026-05-28 07:23'
updated_date: '2026-05-28 09:25'
labels:
  - foundation
  - shared-utility
milestone: foundation
dependencies:
  - TASK-0001
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a `skills/shared/vault_state.py` module providing two functions: `read_state(vault_root)` and `write_state(vault_root, updates)`. Both scripts that currently read/write `.lint/state.yaml` directly must import from this module instead.

`write_state` uses patch semantics: merges `updates` into existing state rather than replacing the whole file. This allows `fetch_inbox.py` to increment `ingests_since_last_lint` without knowing the full state schema.

Also add `load_config(vault_root)` here (not in a separate file) since config loading and state management are both vault-level shared concerns. `load_config` reads `vault.config.yml` using only the standard library, returns a nested dict, and falls back to hardcoded defaults when the file is absent so existing vaults without the file keep working.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 read_state returns a dict with all keys from .lint/state.yaml (or empty dict if file absent)
- [ ] #2 write_state patches the file — missing keys are added, existing keys are updated, unmentioned keys are preserved
- [ ] #3 load_config returns correct defaults when vault.config.yml is absent
- [ ] #4 load_config raises a clear error (not a silent dict KeyError) when the file exists but is malformed
- [ ] #5 No third-party imports — standard library only
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 2** in the implementation plan. Full source code for `skills/shared/vault_state.py` and `tests/test_vault_state.py` is provided — follow TDD: write tests first, run to confirm failure, implement, run to confirm pass. The parser handles only two-level YAML with scalar values and inline lists; block lists (`- item`) are explicitly not supported. Wave 1, step 2 — depends on TASK-0001.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created skills/shared/vault_state.py (stdlib-only: load_config, read_state, write_state) and tests/test_vault_state.py (14 tests, all passing). Fixed inline YAML comment stripping bug during review. Committed on feat-foundation.
<!-- SECTION:FINAL_SUMMARY:END -->
