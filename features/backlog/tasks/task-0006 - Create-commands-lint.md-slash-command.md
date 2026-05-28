---
id: TASK-0006
title: Create commands/lint.md slash command
status: To Do
assignee: []
created_date: '2026-05-28 07:25'
updated_date: '2026-05-28 08:25'
labels:
  - bug-fix
  - lint
  - commands
milestone: bug-fixes
dependencies:
  - TASK-0003
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add `commands/lint.md` following the structure of the four existing command files (`save.md`, `view.md`, `reflect.md`, `forget.md`). The file must describe both the explicit user trigger (`/lint`) and the auto-trigger logic the agent must check at session start.

Auto-trigger condition: read `ingests_since_last_lint` and `last_lint` from `.lint/state.yaml` via the state utility; compare against `lint.auto_trigger_after_ingests` and `lint.auto_trigger_after_days` from `vault.config.yml`. If either threshold is met, run lint before proceeding with the session.

The `init-vault.sh` install loop for commands must also be updated to include `lint`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/lint.md exists and follows the same frontmatter + heading structure as the other command files
- [ ] #2 File documents both /lint explicit trigger and auto-trigger threshold logic
- [ ] #3 Auto-trigger section references vault.config.yml keys by name so the agent knows where to find thresholds
- [ ] #4 init-vault.sh copies commands/lint.md into .claude/commands/lint.md on install/update
- [ ] #5 GETTING-STARTED.md operations table remains consistent with the new file
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 6** in the implementation plan. Full markdown content for `commands/lint.md` is provided — copy verbatim. The file documents both explicit `/lint` trigger and the auto-trigger condition (check `.lint/state.yaml` `ingests_since_last_lint` and `last_lint` against vault.config.yml thresholds). Wave 2 — requires Wave 1 complete, no other Wave 2 dependencies.
<!-- SECTION:NOTES:END -->
