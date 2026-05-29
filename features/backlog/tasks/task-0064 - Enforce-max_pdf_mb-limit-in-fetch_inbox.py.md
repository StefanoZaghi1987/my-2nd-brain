---
id: TASK-0064
title: Enforce max_pdf_mb limit in fetch_inbox.py
status: To Do
assignee: []
created_date: '2026-05-29 11:43'
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
- [ ] #1 A PDF URL whose Content-Length header exceeds max_pdf_mb returns FetchResult(success=False) with a descriptive reason; no file is written
- [ ] #2 A PDF URL with no Content-Length header that exceeds max_pdf_mb mid-stream returns FetchResult(success=False); any partial file is cleaned up
- [ ] #3 A PDF URL within the size limit downloads successfully (regression)
- [ ] #4 Two new tests cover the oversized-with-header and oversized-mid-stream cases; existing tests remain green
<!-- AC:END -->
