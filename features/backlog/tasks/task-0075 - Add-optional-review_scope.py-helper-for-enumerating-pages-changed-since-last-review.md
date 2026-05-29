---
id: TASK-0075
title: >-
  Add optional review_scope.py helper for enumerating pages changed since last
  review
status: To Do
assignee: []
created_date: '2026-05-29 11:45'
labels: []
milestone: m-1
dependencies:
  - TASK-0072
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - skills/shared/review_scope.py
  - init_vault.py
  - tests/test_review_scope.py
priority: low
ordinal: 3300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The REVIEW command's default scope (pages modified since `last_review`) can be determined by the LLM reading frontmatter directly — but a small deterministic helper makes this consistent, testable, and fast on large vaults.

Create `skills/shared/review_scope.py`: a stdlib-only script that reads `.review/state.yaml` for `last_review`, walks `wiki/` for pages whose frontmatter `updated` field is newer, and prints the list. Reuses the `parse_frontmatter()` logic already in `lint.py` (import or copy the relevant function — keep it stdlib-only with no new dependencies).

Install location: `skills/shared/review_scope.py` (alongside `vault_state.py`). Add to `init_vault.py` install step for the shared skill.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 skills/shared/review_scope.py exists and is stdlib-only (no pip dependencies)
- [ ] #2 Given a vault with mixed updated dates, the script prints only pages newer than last_review
- [ ] #3 When last_review is null (first run), the script returns all wiki pages
- [ ] #4 Exit 0 with results, exit 1 with no pages in scope, exit 2 on error
- [ ] #5 At least two tests: one with a prior last_review date (filters correctly), one with null last_review (returns all)
- [ ] #6 init_vault.py installs review_scope.py into .claude/skills/shared/
<!-- AC:END -->
