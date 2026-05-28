---
id: TASK-0030
title: Add missing sixth invariant to README design principles
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
labels:
  - wave-2
  - docs
milestone: vault-hardening
dependencies: []
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
