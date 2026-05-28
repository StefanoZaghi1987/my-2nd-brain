---
id: TASK-0005
title: Migrate lint.py to load config and use vault_state for state I/O
status: Done
assignee: []
created_date: '2026-05-28 07:23'
updated_date: '2026-05-28 09:25'
labels:
  - foundation
  - lint
milestone: foundation
dependencies:
  - TASK-0002
  - TASK-0003
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace all hardcoded threshold constants in `lint.py` with values from `vault.config.yml` via `load_config()`. Replace the inline `write_state()` function and all direct reads/writes to `.lint/state.yaml` with calls to `read_state()` and `write_state()` from `vault_state.py`.

Constants to migrate: `STALE_SOURCE_DAYS`, `VIEW_STALE_DAYS`, `DUPLICATE_SIMILARITY_THRESHOLD`, and the orphan exception path set.

The `--unattended` flag behaviour and all nine lint checks remain unchanged.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 No hardcoded threshold values remain in the script body
- [ ] #2 write_state and read_state calls go through vault_state module
- [ ] #3 Inline write_state function in lint.py is removed
- [ ] #4 All nine checks produce identical findings before and after the migration
- [ ] #5 Script behaves identically when vault.config.yml is absent (defaults apply)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 5** in the implementation plan. This is the largest task: full test file `tests/test_lint.py` plus 9 steps in lint.py. Key changes: vault_state import, remove hardcoded constants, replace local `write_state()` with imported `_write_state`, add `strip_wikilink()` helper, add `check_based_on_links(pages, vault)` (blocking severity), add `check_pdf_index(vault)` (advisory). Register both in `run_lint()` with correct dispatcher branches. Also fulfills TASK-0007 and TASK-0012. Wave 1, parallel with TASK-0004.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Migrated lint.py: imports vault_state (write_state aliased as _write_state to avoid collision), removed STALE_SOURCE_DAYS/VIEW_STALE_DAYS/DUPLICATE_SIMILARITY_THRESHOLD constants, run_lint loads config, replaced inline write_state with _write_state call, added strip_wikilink helper, added check_based_on_links (blocking severity), added check_pdf_index (advisory). Created tests/test_lint.py (11 tests, all passing). Committed on feat-foundation.
<!-- SECTION:FINAL_SUMMARY:END -->
