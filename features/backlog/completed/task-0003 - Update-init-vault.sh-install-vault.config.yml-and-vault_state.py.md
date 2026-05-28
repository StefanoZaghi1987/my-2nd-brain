---
id: TASK-0003
title: 'Update init-vault.sh: install vault.config.yml and vault_state.py'
status: Done
assignee: []
created_date: '2026-05-28 07:23'
updated_date: '2026-05-28 09:25'
labels:
  - foundation
  - bootstrap
milestone: foundation
dependencies:
  - TASK-0001
  - TASK-0002
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend `init-vault.sh` with two new install steps that run after the existing skills installation block:

1. Copy `vault.config.yml` from the bundle root to the vault root — only if the file does not already exist (same guard pattern used for `inbox.md`).
2. Copy `skills/shared/vault_state.py` into `.claude/skills/shared/vault_state.py` in the vault — always refreshed on re-run (same pattern used for skill scripts).

Also add `skills/shared/` to the `DIRS` array so the directory is created before the copy.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Running init-vault.sh on a fresh vault creates vault.config.yml at the vault root
- [ ] #2 Running init-vault.sh on a vault that already has vault.config.yml leaves it untouched
- [ ] #3 Running init-vault.sh always refreshes .claude/skills/shared/vault_state.py
- [ ] #4 .claude/skills/shared/ directory is created before the copy step
- [ ] #5 Script output uses the existing ok/skip/warn helpers consistently
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 3** in the implementation plan. Four changes to init-vault.sh: (1) add `.claude/skills/shared` to DIRS array, (2) install vault.config.yml skipping if user copy exists, (3) install vault_state.py always refreshed, (4) change inbox.md template `## Done` → `## Processed`, (5) add `lint` to command install loop. Verify with `bash init-vault.sh /tmp/test-vault-init`. Wave 1, step 3 — depends on TASK-0002.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Updated init-vault.sh: added .claude/skills/shared to DIRS, vault.config.yml install (skip-if-exists), vault_state.py install (always refreshed), fixed inbox.md header ## Done → ## Processed, extended command loop to include lint. Committed on feat-foundation.
<!-- SECTION:FINAL_SUMMARY:END -->
