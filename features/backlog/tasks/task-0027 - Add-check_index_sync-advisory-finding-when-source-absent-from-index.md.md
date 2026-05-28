---
id: TASK-0027
title: 'Add check_index_sync: advisory finding when source absent from index.md'
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
updated_date: '2026-05-28 12:34'
labels:
  - wave-1
  - linter
milestone: vault-hardening
dependencies:
  - TASK-0026
modified_files:
  - skills/vault-linter/scripts/lint.py
  - tests/test_lint.py
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CLAUDE.md invariant #6 requires updating wiki/index.md after every write, but there is no automated verification. check_index_sync compares every wiki/sources/<slug>.md against the body text of wiki/index.md and reports any slug that does not appear there.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §1.6\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 7
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 check_index_sync returns [] when wiki/index.md is absent
- [ ] #2 Returns [] when every wiki/sources/ slug appears somewhere in wiki/index.md body text
- [ ] #3 Returns one advisory finding per source slug absent from index body text, with check name index_sync
- [ ] #4 Registered in run_lint() under the two-argument dispatcher branch (pages, vault)
- [ ] #5 pytest tests/test_lint.py passes with no regressions
<!-- AC:END -->
