---
id: TASK-0022
title: Fix update_inbox leaving orphaned sub-bullets on successful fetch
status: To Do
assignee: []
created_date: '2026-05-28 12:32'
labels:
  - wave-1
  - fetch
milestone: vault-hardening
dependencies: []
modified_files:
  - skills/inbox-fetcher/scripts/fetch_inbox.py
  - tests/test_fetch_inbox.py
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When a URL entry in inbox.md has indented sub-bullets (`- tags:`, `- note:`) and the fetch succeeds, the URL line is moved to Processed but the sub-bullet lines are left as orphaned content in "To process". On failure the sub-bullets should remain (context for retry); on success they should be dropped (their values have been captured in raw frontmatter).\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §1.1\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 2
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A successfully fetched URL with tags/note sub-bullets produces no sub-bullet lines in the output inbox text
- [ ] #2 A failed URL with tags/note sub-bullets keeps those sub-bullets immediately below the ⚠ line
- [ ] #3 A URL not included in the current batch retains its URL line and sub-bullets unchanged
- [ ] #4 All existing TestUpdateInbox tests continue to pass
- [ ] #5 pytest tests/test_fetch_inbox.py passes with no regressions
<!-- AC:END -->
