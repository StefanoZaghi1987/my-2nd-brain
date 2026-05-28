---
id: TASK-0034
title: Add Obsidian minimal skeleton to init-vault.sh
status: To Do
assignee: []
created_date: '2026-05-28 12:34'
labels:
  - wave-2
  - obsidian
milestone: vault-hardening
dependencies: []
modified_files:
  - init-vault.sh
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The vault is Obsidian-compatible but ships no Obsidian config. Without useMarkdownLinks: false, Obsidian writes [text](path) markdown links instead of [[wikilinks]], which the vault linter cannot track as wiki links — dead-link detection and orphan checks silently miss them.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §2.7\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 14
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 .obsidian is in the DIRS array so the directory is created on bootstrap
- [ ] #2 .obsidian/app.json is created with useMarkdownLinks: false, newLinkFormat: relative, readableLineLength: true, attachmentFolderPath: wiki/views/assets
- [ ] #3 Creation is skipped if .obsidian/app.json already exists
- [ ] #4 Running init-vault.sh against a fresh directory produces a valid .obsidian/app.json
<!-- AC:END -->
