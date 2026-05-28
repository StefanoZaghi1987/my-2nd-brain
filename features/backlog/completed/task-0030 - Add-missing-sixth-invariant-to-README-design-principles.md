---
id: TASK-0030
title: Add missing sixth invariant to README design principles
status: Done
assignee: []
created_date: '2026-05-28 12:33'
updated_date: '2026-05-28 13:41'
labels:
  - wave-2
  - docs
milestone: vault-hardening
dependencies: []
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-10
modified_files:
  - README.md
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
README.md ## Design principles says "Five invariants" and lists five. CLAUDE.md defines six. The missing one is the ≤15 files per operation constraint, which is enforced by the agent and checked by linter cascade logic.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §2.3\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 10
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Heading reads Six invariants
- [ ] #2 New entry states: Touch ≤15 files per operation; stop and ask if more are needed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
In `README.md`, find the `## Design principles` section. Change the heading line from "Five invariants:" to "Six invariants:". Add a sixth numbered entry after entry 5: `6. **Touch ≤15 files per operation.** If more are needed, stop and ask — split the work across sessions.` No tests needed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Changed "Five invariants:" to "Six invariants:" in README.md `## Design principles` and added the missing 6th: "Touch ≤15 files per operation. If more are needed, stop and ask — split the work across sessions." Commit: 58bd0ff.
<!-- SECTION:FINAL_SUMMARY:END -->
