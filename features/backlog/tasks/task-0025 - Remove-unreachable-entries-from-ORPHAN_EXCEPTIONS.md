---
id: TASK-0025
title: Remove unreachable entries from ORPHAN_EXCEPTIONS
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
labels:
  - wave-1
  - linter
milestone: vault-hardening
dependencies: []
modified_files:
  - skills/vault-linter/scripts/lint.py
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
lint.py ORPHAN_EXCEPTIONS contains "index.md" and "log.md" without the wiki/ prefix. load_wiki() stores all paths as vault-relative strings starting with "wiki/", so these bare entries can never match anything and provide no protection.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §1.4\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 5
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ORPHAN_EXCEPTIONS contains exactly four entries: wiki/hot.md, wiki/compass.md, wiki/index.md, wiki/log.md
- [ ] #2 pytest tests/test_lint.py passes with no regressions
<!-- AC:END -->
