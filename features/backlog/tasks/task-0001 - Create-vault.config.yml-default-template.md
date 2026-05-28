---
id: TASK-0001
title: Create vault.config.yml default template
status: Done
assignee: []
created_date: '2026-05-28 07:23'
updated_date: '2026-05-28 09:25'
labels:
  - foundation
  - config
milestone: foundation
dependencies: []
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a `vault.config.yml` file to the bundle root that defines all configurable vault parameters with their default values. This file becomes the single source of truth for every value currently hardcoded across Python scripts and CLAUDE.md.

The file must cover these sections: `vault.version`, `inbox.processed_section`, `inbox.tags_propagation`, `fetch.*` (timeouts, size limits, pdf_enabled, walled_domains), `lint.*` (staleness thresholds, auto-trigger counters), `ingest.*` (max pages before confirm, max files per operation).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 vault.config.yml exists at the bundle root with all config sections
- [ ] #2 Every value currently hardcoded in fetch_inbox.py and lint.py has a corresponding key
- [ ] #3 File is valid YAML parseable by Python's standard library (no third-party YAML parser required)
- [ ] #4 Each key has an inline comment explaining its effect (one line max)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 1** in the implementation plan. Full YAML content with inline comments is provided — copy it exactly. Key constraint: walled_domains must use inline list syntax `[a, b]`, not block list, because the stdlib parser in vault_state.py only handles inline. Wave 1, step 1 — must be done before TASK-0002.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created vault.config.yml at bundle root with all tunable defaults. Inline YAML comments parse correctly. Committed on feat-foundation.
<!-- SECTION:FINAL_SUMMARY:END -->
