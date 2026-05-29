---
id: TASK-0065
title: Honour inbox.tags_propagation config flag in fetch_inbox.py
status: Done
assignee: []
created_date: '2026-05-29 11:43'
updated_date: '2026-05-29 15:03'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - skills/inbox-fetcher/scripts/fetch_inbox.py
  - tests/test_fetch_inbox.py
priority: low
ordinal: 1400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The `inbox.tags_propagation` config key has been present in `vault.config.yml` and `vault_state.py` `_DEFAULTS` since the first design phase — but `fetch_inbox.py` ignores it and always propagates `tags`/`note` from inbox sub-bullets into `raw/` frontmatter.

Wrap the propagation block so it only runs when the config flag is true (default: `True`, preserving current behaviour). This lets operators disable automatic tag carry-over when they prefer to tag wiki sources manually.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 When vault.config.yml sets inbox.tags_propagation: false, fetched sources have no tags or note in their raw/ index.md frontmatter
- [x] #2 When vault.config.yml sets inbox.tags_propagation: true (or the key is absent), tags and note are propagated as before
- [x] #3 One new test covers the tags_propagation: false case; existing propagation tests remain green
<!-- AC:END -->



## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
_should_propagate_tags() helper; propagate_tags param in both fetch functions; all 3 call sites in process_vault() wired. Integration test exercises config→callsite path. 25/25 pass. Commit 35c5b41.
<!-- SECTION:FINAL_SUMMARY:END -->
