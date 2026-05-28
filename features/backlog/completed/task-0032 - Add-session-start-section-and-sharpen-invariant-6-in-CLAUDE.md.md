---
id: TASK-0032
title: Add session-start section and sharpen invariant 6 in CLAUDE.md
status: Done
assignee: []
created_date: '2026-05-28 12:33'
updated_date: '2026-05-28 13:41'
labels:
  - wave-2
  - docs
milestone: vault-hardening
dependencies:
  - TASK-0021
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-12
modified_files:
  - CLAUDE.md
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The auto-lint trigger conditions are documented only in commands/lint.md. The reflect reminder (reflect_reminder_days) has no session-start hook in the agent contract at all. CLAUDE.md is the authoritative operating contract the agent reads first — session lifecycle rules belong there.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §2.5 and §2.8\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 12
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 New ## Session start section exists between ## Hot cache and ## Unattended mode
- [ ] #2 Section lists three numbered steps: read hot.md, check lint state against lint.auto_trigger_after_ingests and lint.auto_trigger_after_days, suggest /reflect if compass.md age exceeds lint.reflect_reminder_days
- [ ] #3 Config keys are referenced by their vault.config.yml names
- [ ] #4 Invariant #6 text uses full paths wiki/index.md and wiki/log.md and clarifies what updating each means
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Two edits in `CLAUDE.md`. (1) Find the `## Hot cache` section and the `## Unattended mode` section that follows it. Insert a new `## Session start` section between them. The section has three numbered steps: read wiki/hot.md; check .lint/state.yaml against `lint.auto_trigger_after_ingests` and `lint.auto_trigger_after_days`; suggest /reflect if compass.md age exceeds `lint.reflect_reminder_days`. Config keys must be quoted by their vault.config.yml names. Full text in plan Task 12 Step 1. (2) In the `## Six invariants` section, find invariant #6. Replace the current text (which uses bare filenames) with text specifying `wiki/index.md` and `wiki/log.md` and clarifying what "updating" each means. Full text in plan Task 12 Step 2. This task depends on TASK-0021 (the reflect_reminder_days key must exist before it can be referenced). No tests needed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Inserted `## Session start` section in CLAUDE.md between `## Hot cache` and `## Unattended mode` with 3 numbered steps (read hot.md, check .lint/state.yaml auto-lint conditions, suggest /reflect if compass.md is stale). Sharpened invariant #6 to use full `wiki/` paths and explain what "update" means concretely. Commit: 0c7840f.
<!-- SECTION:FINAL_SUMMARY:END -->
