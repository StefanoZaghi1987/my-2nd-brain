---
id: TASK-0064
title: Enforce max_pdf_mb limit in fetch_inbox.py
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
priority: medium
ordinal: 1300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In `skills/inbox-fetcher/scripts/fetch_inbox.py`, the `max_pdf_mb` config key is read and a warning is printed when `Content-Length` exceeds the limit (line ~188) — but the download proceeds in full regardless. Two gaps: (1) the limit is never actually enforced; (2) when the `Content-Length` header is absent, `size = 0` so the check is silently skipped even for very large files.

Required changes:
- After the size check, return a failed `FetchResult` with a clear reason message instead of continuing.
- When `Content-Length` is absent: stream the download in chunks, abort and clean up the partial file if accumulated bytes exceed the limit.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A PDF URL whose Content-Length header exceeds max_pdf_mb returns FetchResult(success=False) with a descriptive reason; no file is written
- [x] #2 A PDF URL with no Content-Length header that exceeds max_pdf_mb mid-stream returns FetchResult(success=False); any partial file is cleaned up
- [x] #3 A PDF URL within the size limit downloads successfully (regression)
- [x] #4 Two new tests cover the oversized-with-header and oversized-mid-stream cases; existing tests remain green
<!-- AC:END -->



## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Fail-fast on Content-Length header + overflow-flag stream-abort for Windows compatibility. Both new tests pass. 22/22. TDD confirmed. Reviewer noted cleanup dedup as optional improvement. Commit 166e651.
<!-- SECTION:FINAL_SUMMARY:END -->
