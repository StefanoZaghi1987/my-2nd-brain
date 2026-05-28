---
id: TASK-0018
title: Add provides/config_section/requires fields to all skill SKILL.md frontmatter
status: Done
assignee: []
created_date: '2026-05-28 07:41'
updated_date: '2026-05-28 10:29'
labels:
  - skill-manifest
  - foundation
milestone: features
dependencies: []
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: low
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add three frontmatter fields to each of the three existing skill files. No other content changes.

**skills/inbox-fetcher/SKILL.md:**
```yaml
provides: fetch
config_section: fetch
requires:
  python: ">=3.10"
  packages: [trafilatura, requests, python-slugify]
```

**skills/vault-linter/SKILL.md:**
```yaml
provides: lint
config_section: lint
requires:
  python: ">=3.10"
  packages: []
```

**skills/view-builder/SKILL.md:**
```yaml
provides: view
config_section: null
requires:
  python: ">=3.10"
  packages: [matplotlib]
```

Note: matplotlib is listed as optional for view-builder (charts only). The SKILL.md body already documents this — the frontmatter just makes it machine-readable for init-vault.sh.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All three SKILL.md files have provides, config_section, and requires fields in frontmatter
- [x] #2 inbox-fetcher requires lists trafilatura, requests, python-slugify
- [x] #3 vault-linter requires lists an empty packages array
- [x] #4 view-builder config_section is null (no config block)
- [x] #5 No body content of any SKILL.md file is modified
<!-- AC:END -->



## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 18** in the implementation plan. Add three frontmatter fields to each SKILL.md: `provides`, `config_section`, `requires`. Values per skill: inbox-fetcher (`provides: fetch`, `config_section: fetch`, packages: `[trafilatura, requests, python-slugify]`); vault-linter (`provides: lint`, `config_section: lint`, packages: `[]`); view-builder (`provides: view`, `config_section: null`, packages: `[matplotlib]`). Wave 3 — independent, no dependencies.
<!-- SECTION:NOTES:END -->
