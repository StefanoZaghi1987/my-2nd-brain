---
id: TASK-0020
title: Add skill dispatch table section to CLAUDE.md
status: Done
assignee: []
created_date: '2026-05-28 07:41'
updated_date: '2026-05-28 10:44'
labels:
  - skill-manifest
  - claude-md
milestone: features
dependencies:
  - TASK-0016
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: low
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a new "## Skill dispatch" section to CLAUDE.md immediately after the Nine operations section. The section contains a single markdown table mapping each operation to its skill and backing implementation. No prose.

| Operation | Skill | Backed by |
|-----------|-------|-----------|
| FETCH | inbox-fetcher | scripts/fetch_inbox.py |
| LINT | vault-linter | scripts/lint.py |
| VIEW | view-builder | templates/ + LLM |
| INGEST | (LLM only) | — |
| QUERY | (LLM only) | — |
| REFLECT | (LLM only) | — |
| PROMOTE | (LLM only) | — |
| REFRESH | (LLM only) | — |

This is the only change to CLAUDE.md in this task.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Skill dispatch section exists in CLAUDE.md after the operations section
- [ ] #2 Table contains all nine operations
- [ ] #3 Table columns are: Operation, Skill, Backed by
- [ ] #4 LLM-only operations show (LLM only) in the Skill column and — in Backed by
- [ ] #5 No prose is added — the table is the entire section content
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**ALREADY FULFILLED by TASK-0016.** The "## Skill dispatch" table is added to CLAUDE.md in Task 16 Step 4 of the plan. See **Task 20** in the plan — verification only. Confirm the `## Skill dispatch` section exists in CLAUDE.md after TASK-0016 is complete. No new work needed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Skill dispatch table added to CLAUDE.md as part of TASK-0016. Table appears at lines 195-207 with all 9 operations (FETCH, LINT, VIEW, INGEST, QUERY, REFLECT, PROMOTE, REFRESH). LLM-only operations correctly show (LLM only) in Skill column and — in Backed by.
<!-- SECTION:FINAL_SUMMARY:END -->
