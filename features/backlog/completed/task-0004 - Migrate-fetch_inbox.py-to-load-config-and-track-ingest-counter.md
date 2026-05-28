---
id: TASK-0004
title: Migrate fetch_inbox.py to load config and track ingest counter
status: Done
assignee: []
created_date: '2026-05-28 07:23'
updated_date: '2026-05-28 09:25'
labels:
  - foundation
  - fetch
milestone: foundation
dependencies:
  - TASK-0002
  - TASK-0003
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace all hardcoded constants in `fetch_inbox.py` with values read from `vault.config.yml` via `load_config()` from `vault_state.py`. After each successful fetch run (at least one URL processed successfully), increment `ingests_since_last_lint` in `.lint/state.yaml` via `write_state()`.

Constants to migrate: `HTML_TIMEOUT`, `PDF_TIMEOUT`, `MAX_PDF_SIZE_MB`, `WALLED_DOMAINS`, and the processed section header string used in `update_inbox()`.

The import of `vault_state` must use a path relative to the script's own location so it works whether invoked from the vault root or from outside via `--vault`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 No hardcoded timeout, size, or domain values remain in the script body
- [ ] #2 Processed section header comes from config (inbox.processed_section)
- [ ] #3 ingests_since_last_lint is incremented by 1 after a run where at least one URL succeeded
- [ ] #4 Script behaves identically when vault.config.yml is absent (defaults apply)
- [ ] #5 Importing vault_state does not fail when script is run from any working directory
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 4** in the implementation plan. Full test file `tests/test_fetch_inbox.py` and all code changes provided. Key changes: (a) vault_state import via `_sys.path.insert` relative to script location, (b) add `tags: list` and `note: str | None` to InboxEntry dataclass, (c) update `find_unchecked_entries()` to parse indented sub-bullets, (d) add `processed_section` param to `update_inbox()`, (e) load config in `process_vault()`, (f) call `write_state()` after successful fetches. Wave 1, parallel with TASK-0005 — both depend on TASK-0003.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Migrated fetch_inbox.py: imports vault_state, InboxEntry gains tags/note fields, find_unchecked_entries parses sub-bullets, update_inbox accepts processed_section param (replacing hardcoded Processati), process_vault loads config, ingest counter increments on success. Created tests/test_fetch_inbox.py (11 tests, all passing). Committed on feat-foundation.
<!-- SECTION:FINAL_SUMMARY:END -->
