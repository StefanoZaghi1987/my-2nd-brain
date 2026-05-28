---
id: TASK-0012
title: Add advisory lint check for raw/papers subfolders missing index.md
status: To Do
assignee: []
created_date: '2026-05-28 07:32'
updated_date: '2026-05-28 08:25'
labels:
  - feature-a
  - lint
milestone: features
dependencies:
  - TASK-0005
  - TASK-0010
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: low
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add `check_pdf_index(vault)` to `lint.py` that scans `raw/papers/` for subdirectories that do not contain an `index.md` file. Each such directory produces an **advisory** finding under check name `missing_pdf_index`.

This catches PDFs that were fetched before the folder-structure convention was adopted, or PDFs dropped manually into `raw/papers/` without an accompanying `index.md`.

Also scan for orphan flat `.pdf` files directly inside `raw/papers/` (not inside a subdirectory) — these are legacy flat-structure PDFs and also produce an advisory finding under `legacy_flat_pdf`.

Register both checks in `run_lint()`. Neither requires the `pages` dict — they only need `vault` (filesystem scan only).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 check_pdf_index produces advisory findings for raw/papers/ subdirs without index.md
- [ ] #2 Flat .pdf files directly in raw/papers/ produce advisory findings under legacy_flat_pdf
- [ ] #3 A correctly structured raw/papers/<slug>/paper.pdf + index.md produces no findings
- [ ] #4 Both checks appear in the lint report grouped under their check names
- [ ] #5 An empty raw/papers/ directory produces no findings
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**ALREADY FULFILLED by TASK-0005.** `check_pdf_index()` is implemented in Task 5 of the plan (lint.py migration). See **Task 12** in the plan — verification only. Run `pytest tests/test_lint.py::TestCheckPdfIndex -v` to confirm. No new code to write.
<!-- SECTION:NOTES:END -->
