---
id: TASK-0076
title: >-
  Add find_backlinks.py helper — enumerate all wiki files linking to a target
  page
status: To Do
assignee: []
created_date: '2026-05-29 11:45'
labels: []
milestone: m-2
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - skills/shared/find_backlinks.py
  - init_vault.py
  - tests/test_find_backlinks.py
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The MERGE operation needs to rewrite every `[[wikilink]]` that points to a page being merged away. Create a small, stdlib-only helper script that takes a vault root and a target page path, and prints every wiki file that links to it.

Install at `skills/shared/find_backlinks.py` alongside `vault_state.py`. The link-resolution logic must match `lint.py`'s `normalize_link_target()` exactly — don't reinvent it. Either import it or copy the function verbatim with a comment pointing to the source.

CLI interface:
```
python find_backlinks.py <vault_root> <target_page_path>
```
Exit 0: found (file list to stdout, one per line). Exit 1: none found. Exit 2: error.

This helper is the only testable script in Phase 3; MERGE itself is LLM-only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 skills/shared/find_backlinks.py exists and is stdlib-only
- [ ] #2 Given a vault fixture with known links, the script returns exactly the files linking to the target
- [ ] #3 Link resolution matches lint.py normalize_link_target() — same handling of .md extension, vault-relative vs source-relative paths
- [ ] #4 Exit codes: 0 (found), 1 (none found), 2 (error / bad args)
- [ ] #5 Tests cover: direct match, match via .md extension, no matches, multiple files linking to same target, dot-containing slug (e.g. arxiv-2602.20867)
- [ ] #6 init_vault.py installs find_backlinks.py into .claude/skills/shared/
<!-- AC:END -->
