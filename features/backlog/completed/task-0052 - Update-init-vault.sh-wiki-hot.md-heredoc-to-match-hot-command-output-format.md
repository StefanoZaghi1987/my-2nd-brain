---
id: TASK-0052
title: Update init-vault.sh wiki/hot.md heredoc to match /hot command output format
status: Done
assignee: []
created_date: '2026-05-28 16:06'
updated_date: '2026-05-28 16:47'
labels:
  - bug-fix
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - init-vault.sh
priority: low
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix three heredocs in `init-vault.sh`:
1. `wiki/hot.md` heredoc content should match what `/hot` command produces (no YAML frontmatter, no section headers)
2. `.lint/state.yaml` should use `fetches_since_last_lint` (not `ingests_since_last_lint`)
3. `.lint/report.md` should reference `python3` (not `python`)

Also fixes .lint/state.yaml heredoc key name and .lint/report.md python→python3
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 #1 The `wiki/hot.md` heredoc emits content matching the structure produced by the /hot command
- [ ] #2 #2 The `.lint/state.yaml` heredoc emits `fetches_since_last_lint: 0` (not `ingests_since_last_lint: 0`)
- [ ] #3 #3 The `.lint/report.md` heredoc references `python3 .claude/skills/vault-linter/scripts/lint.py` (not `python …`)
<!-- AC:END -->
