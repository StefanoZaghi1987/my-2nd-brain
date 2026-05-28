---
id: TASK-0027
title: 'Add check_index_sync: advisory finding when source absent from index.md'
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
updated_date: '2026-05-28 12:41'
labels:
  - wave-1
  - linter
milestone: vault-hardening
dependencies:
  - TASK-0026
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-7
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
In `skills/vault-linter/scripts/lint.py`: (1) Add `check_index_sync(pages: dict[str, WikiPage], vault: Path) -> list[Finding]` after `check_conversations`. It gets `pages.get("wiki/index.md")`, reads its `body_text`, then for each `wiki/sources/<slug>.md` checks if `Path(rel).stem` (the slug) appears as a substring of the index body. Advisory finding with check name `index_sync` when missing. Full function in plan Task 7 Step 3. (2) In `run_lint()` add `("index_sync", check_index_sync)` to `all_checks`. (3) Update the two-argument dispatcher branch to: `if name in ("dead_links", "orphans", "based_on_dead_links", "index_sync"):`. Full registration in plan Task 7 Step 4. This task must be done after TASK-0026 since both edit the same dispatcher block. Test: `pytest tests/test_lint.py -v`
<!-- SECTION:NOTES:END -->
