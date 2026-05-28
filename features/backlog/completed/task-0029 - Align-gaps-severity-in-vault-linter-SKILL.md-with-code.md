---
id: TASK-0029
title: Align gaps severity in vault-linter SKILL.md with code
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
  - features/plans/2026-05-28-vault-hardening-plan.md#task-9
modified_files:
  - skills/vault-linter/SKILL.md
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The ## Output section of skills/vault-linter/SKILL.md lists "gaps" under Important findings. The check_gaps() function emits severity="advisory". The documentation contradicts the implementation. The ~30% false-positive rate on gap findings makes advisory the correct level.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §2.2\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 9
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Important section lists only orphans
- [ ] #2 Advisory section lists duplicates, stale, naming, view staleness, gaps, and missing cross-references
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
In `skills/vault-linter/SKILL.md`, find the `## Output` section, then the `.lint/report.md` subsection. Find the two bullet lines: `- **Important** — orphans, gaps.` and `- **Advisory** — duplicates, stale, naming, view staleness.` Replace them with: `- **Important** — orphans.` and `- **Advisory** — duplicates, stale, naming, view staleness, gaps, missing cross-references.` No tests needed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Moved `gaps` from Important to Advisory in `skills/vault-linter/SKILL.md` severity table. Also added `missing cross-references` to Advisory. Aligns docs with the `severity="advisory"` the code has always emitted for gaps. Commit: dee2cea.
<!-- SECTION:FINAL_SUMMARY:END -->
