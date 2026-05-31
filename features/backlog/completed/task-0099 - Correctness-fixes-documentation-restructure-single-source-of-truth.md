---
id: TASK-0099
title: Correctness fixes + documentation restructure (single-source-of-truth)
status: Done
assignee: []
created_date: '2026-05-30 23:33'
updated_date: '2026-05-31 00:42'
labels:
  - documentation
  - correctness
  - installer
milestone: m-6
dependencies: []
references:
  - features/specs/2026-05-31-llm-wiki-correctness-docs-design.md
  - features/plans/2026-05-31-llm-wiki-correctness-docs-plan.md
documentation:
  - features/specs/2026-05-31-llm-wiki-correctness-docs-design.md
  - features/plans/2026-05-31-llm-wiki-correctness-docs-plan.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A full audit identified two categories of real issues in the vault engine:

1. **Correctness gaps** — compass.md referenced but never scaffolded on fresh vaults; installer script list hardcoded and silently drops new scripts; review.max_faithfulness_pages undocumented in config; operation/command count mismatch in headings.
2. **Documentation drift** — the "six invariants" disagree across CLAUDE.md vs README/GETTING-STARTED, a direct symptom of duplicated counted lists living in three files.

This parent task tracks the full fix. All implementation detail, exact code, and replacement content is in the plan and spec referenced below.

**Branch:** feat-hotfix  
**Spec:** features/specs/2026-05-31-llm-wiki-correctness-docs-design.md  
**Plan:** features/plans/2026-05-31-llm-wiki-correctness-docs-plan.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 11 pytest modules pass with no regressions
- [ ] #2 No doc claims a hardcoded invariant/operation count that can drift
- [ ] #3 Single authoritative tiered invariants list exists only in CLAUDE.md; README and GETTING-STARTED link to it
- [ ] #4 vault.config.yml review: block and vault_state.py _DEFAULTS both contain max_faithfulness_pages: 10
- [ ] #5 Fresh vault (python init_vault.py --yes) bootstraps without referencing non-existent compass.md
- [ ] #6 Installer auto-discovers new .py scripts; test_*.py excluded
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
All 9 subtasks complete across 7 files. Commits: 0819b2d (config), d8a48ba (TDD red), 514e9c6 (spec/plan .sh extension), 1c35616 (installer auto-discovery), 5e4cd5a (CLAUDE.md tiered invariants), d3142e6 (CLAUDE.md mechanical), 8958b76 (GS headings), 43de424 (GS content), c8af2d7 (README), ceaabab (banner+verify). 204/204 tests green. Drift eliminated. Single-source-of-truth enforced.
<!-- SECTION:FINAL_SUMMARY:END -->
