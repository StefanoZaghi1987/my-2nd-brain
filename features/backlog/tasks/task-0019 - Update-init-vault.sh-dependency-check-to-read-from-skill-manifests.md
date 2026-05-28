---
id: TASK-0019
title: Update init-vault.sh dependency check to read from skill manifests
status: To Do
assignee: []
created_date: '2026-05-28 07:41'
updated_date: '2026-05-28 08:26'
labels:
  - skill-manifest
  - bootstrap
milestone: features
dependencies:
  - TASK-0018
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: low
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the hardcoded `missing=()` loop in `init-vault.sh` that checks for `trafilatura requests slugify` with a loop that reads `requires.packages` from each installed skill's `SKILL.md` frontmatter.

The script must extract package names from lines matching `  packages: [...]` inside the SKILL.md frontmatter block, split them by comma, and deduplicate before checking. Use only shell built-ins and `grep`/`sed` — no Python or YAML parser.

This makes the dependency check self-maintaining: when a new skill with new packages is added to the bundle, the check picks them up without any change to `init-vault.sh`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Dependency check reads packages from SKILL.md files rather than a hardcoded list
- [ ] #2 All packages from all installed skills are checked (deduplicated)
- [ ] #3 The check still uses python3 -c 'import <pkg>' for each package
- [ ] #4 Missing packages are reported with the same warn/ok output format as before
- [ ] #5 The check works correctly when a skill has an empty packages list
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 19** in the implementation plan. Replace the hardcoded `missing=()` loop in init-vault.sh with a manifest-driven loop: iterate `"$VAULT_DIR"/.claude/skills/*/SKILL.md`, extract `packages:` line with grep/sed, deduplicate, check each with `python3 -c "import $pkg"`. Full bash replacement block provided. Depends on TASK-0018 being done first so the SKILL.md files have the `packages:` field. Wave 3 — depends on TASK-0018.
<!-- SECTION:NOTES:END -->
