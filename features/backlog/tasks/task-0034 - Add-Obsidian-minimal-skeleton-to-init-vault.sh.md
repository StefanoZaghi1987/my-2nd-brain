---
id: TASK-0034
title: Add Obsidian minimal skeleton to init-vault.sh
status: To Do
assignee: []
created_date: '2026-05-28 12:34'
updated_date: '2026-05-28 12:40'
labels:
  - wave-2
  - obsidian
milestone: vault-hardening
dependencies:
  - TASK-0031
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-14
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
In `init-vault.sh`: (1) Find the DIRS=( block (~line 87) and add `".obsidian"` as the last entry before the closing ). (2) After the `.gitignore` creation block (the line `ok ".gitignore"`), insert the new `# --- Obsidian config` section that creates `.obsidian/app.json` using a heredoc (skip if file already exists). The JSON must include `useMarkdownLinks: false` — this is the critical field that keeps Obsidian writing [[wikilinks]] instead of [text](path) links. Full bash code in plan Task 14 Steps 1-2. Verify with: `bash init-vault.sh /tmp/test-vault && cat /tmp/test-vault/.obsidian/app.json && rm -rf /tmp/test-vault`
<!-- SECTION:NOTES:END -->
