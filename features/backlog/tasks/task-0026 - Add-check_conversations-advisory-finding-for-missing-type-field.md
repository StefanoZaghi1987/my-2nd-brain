---
id: TASK-0026
title: 'Add check_conversations: advisory finding for missing type field'
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
labels:
  - wave-1
  - linter
milestone: vault-hardening
dependencies: []
modified_files:
  - skills/vault-linter/scripts/lint.py
  - tests/test_lint.py
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Conversation files in conversations/ have no enforced frontmatter schema. A linter check for `type: conversation` makes the schema discoverable. Severity is advisory — existing conversations without the field are grandfathered rather than treated as blocking errors.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §1.5\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 6
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 check_conversations(vault) returns [] when conversations/ directory is absent
- [ ] #2 Conversation files with type: conversation produce no findings
- [ ] #3 Conversation files missing type: conversation produce one advisory finding with check name missing_conversation_type
- [ ] #4 The check is registered in run_lint() and its findings appear in .lint/report.md
- [ ] #5 pytest tests/test_lint.py passes with no regressions
<!-- AC:END -->
