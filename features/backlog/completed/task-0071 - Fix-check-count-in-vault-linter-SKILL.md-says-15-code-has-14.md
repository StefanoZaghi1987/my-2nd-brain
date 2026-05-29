---
id: TASK-0071
title: 'Fix check count in vault-linter SKILL.md (says 15, code has 14)'
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
  - skills/vault-linter/SKILL.md
priority: low
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`skills/vault-linter/SKILL.md` states "15 deterministic checks" in its description of the linter's capabilities. The actual `lint.py` `all_checks` list (line ~787) contains exactly 14 check functions. One-line documentation fix — the number should match the code.

The 14 checks are: `dead_links`, `based_on_dead_links`, `pdf_index`, `drop_zone`, `orphans`, `duplicates`, `missing_metadata`, `inconsistent_naming`, `stale_sources`, `gaps`, `view_staleness`, `missing_cross_references`, `conversations`, `index_sync`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 SKILL.md states '14 deterministic checks' (or equivalent accurate phrasing)
- [x] #2 Grep for '15' near the check-count sentence in SKILL.md returns zero matches
- [x] #3 The 14 check names listed in the spec description are consistent with what is in lint.py all_checks
<!-- AC:END -->



## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Full reconciliation: merged table rows #11+#14 into single PDF index row, renumbered to 14, updated YAML description and advisory list. Commit 620bba1. Clean — no remaining "Fifteen" references.
<!-- SECTION:FINAL_SUMMARY:END -->
