---
id: TASK-0021
title: Add reflect_reminder_days config key
status: To Do
assignee: []
created_date: '2026-05-28 12:32'
labels:
  - wave-1
  - config
milestone: vault-hardening
dependencies: []
modified_files:
  - vault.config.yml
  - skills/shared/vault_state.py
  - tests/test_vault_state.py
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The vault config has auto-lint triggers (`auto_trigger_after_ingests`, `auto_trigger_after_days`) but no equivalent threshold for suggesting `/reflect`. The session-start protocol in CLAUDE.md needs a configurable value to compare against the age of `wiki/compass.md`.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §1.7\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 1
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 vault.config.yml has reflect_reminder_days: 14 in the lint: section
- [ ] #2 vault_state.py _DEFAULTS["lint"] includes "reflect_reminder_days": 14
- [ ] #3 TestLoadConfig.test_returns_all_default_sections_when_absent asserts config["lint"]["reflect_reminder_days"] == 14
- [ ] #4 pytest tests/test_vault_state.py passes with no regressions
<!-- AC:END -->
