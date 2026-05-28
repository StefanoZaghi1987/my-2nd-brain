---
id: TASK-0031
title: Create commands/ingest.md and register it in init-vault.sh
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
labels:
  - wave-2
  - commands
milestone: vault-hardening
dependencies: []
modified_files:
  - commands/ingest.md
  - init-vault.sh
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
INGEST is the vault's primary write operation but has no slash command file. Every other named operation (save, view, reflect, forget, lint, promote, refresh) has one. A new conversation can reconstruct FETCH and LINT from skill files but has no equivalent compact protocol sheet for INGEST.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §2.4\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 11
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/ingest.md exists with: YAML frontmatter description, trigger conditions, target discovery logic, web article protocol, PDF protocol, guards (≤3 new pages, ≤15 files), and completion steps (index.md + log.md)
- [ ] #2 init-vault.sh command loop includes ingest
- [ ] #3 Running init-vault.sh against a fresh directory produces .claude/commands/ingest.md
<!-- AC:END -->
