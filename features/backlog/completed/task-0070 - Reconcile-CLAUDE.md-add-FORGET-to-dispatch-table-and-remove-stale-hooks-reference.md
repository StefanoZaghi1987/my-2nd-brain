---
id: TASK-0070
title: >-
  Reconcile CLAUDE.md: add FORGET to dispatch table and remove stale hooks
  reference
status: Done
assignee: []
created_date: '2026-05-29 11:44'
updated_date: '2026-05-29 15:03'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - CLAUDE.md
priority: medium
ordinal: 1900
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two inconsistencies in `CLAUDE.md` erode it as an authoritative contract:

1. **Missing dispatch table row**: The header says "Nine operations" and the operations section lists all nine (FETCH, INGEST, FORGET, QUERY, VIEW, REFLECT, LINT, PROMOTE, REFRESH), but the "Skill dispatch" table at line ~225 has only 8 rows — FORGET is absent. It has its own `commands/forget.md` and is fully operational; it simply was never added to the table.

2. **Stale hooks claim**: Line 33 lists `.claude/` contents as "Skills, commands, hooks (mechanisms, not content)". No hooks exist anywhere: no `.claude/hooks/` directory, no `hooks` key in any settings file, and `init_vault.py` never installs any hooks. This claim misleads anyone reading the contract.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Skill dispatch table has 9 rows, including a FORGET row: `FORGET | (LLM only) | —`
- [x] #2 Line 33 (or wherever the .claude/ directory description appears) no longer mentions 'hooks'
- [x] #3 Grep for 'hooks' in CLAUDE.md returns zero matches in the directory-listing context (non-hooks uses like 'workflow hooks' are fine if present elsewhere)
<!-- AC:END -->



## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added FORGET row to dispatch table (9 rows total). Removed 'hooks' from .claude/ dir listing. Also added missing Local Markdown deletion branch to FORGET step 5. Three commits: bf65ed2 (main fix) + f64f4c3 (Local Markdown branch). CLAUDE.md is now internally consistent — INGEST 4 source types match FORGET 4 deletion branches.
<!-- SECTION:FINAL_SUMMARY:END -->
