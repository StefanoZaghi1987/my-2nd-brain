---
id: TASK-0073
title: Add REVIEW operation to CLAUDE.md (operations section + dispatch table)
status: To Do
assignee: []
created_date: '2026-05-29 11:44'
labels: []
milestone: m-1
dependencies:
  - TASK-0072
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - CLAUDE.md
priority: high
ordinal: 3100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add REVIEW as the tenth operation in `CLAUDE.md`. This involves three changes to the file:

1. **Operations section**: Add a new REVIEW section after REFLECT, following the same structure as existing operations. Key points: when to invoke, what it does, that it's report-only, and that it uses scoping to control token cost.

2. **Dispatch table**: Add the row `REVIEW | (LLM only) | —` and update the heading from "Nine operations" to "Ten operations".

3. **Unattended mode**: Add REVIEW to the "CAN" list — it reads pages and writes `.review/report.md` but applies no structural changes, making it unattended-safe.

4. **Session-start**: Explicitly note REVIEW has NO auto-trigger (unlike LINT) — semantic cost is opt-in by design.

Depends on task-0072 (commands/review.md) being authored first so the protocol details are available.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 CLAUDE.md has a REVIEW operation section describing the three checks and scoping
- [ ] #2 Dispatch table includes REVIEW row and heading says 'Ten operations'
- [ ] #3 Unattended mode CAN list includes 'run REVIEW, update .review/report.md'
- [ ] #4 Session-start section or REVIEW section explicitly states no auto-trigger for REVIEW
- [ ] #5 CLAUDE.md operation count is consistent throughout (Ten in heading, 10 rows in table, 10 sections)
<!-- AC:END -->
