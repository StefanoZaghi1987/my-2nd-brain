---
id: TASK-0024
title: Route PDF responses without .pdf suffix via Content-Type header
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
updated_date: '2026-05-28 12:34'
labels:
  - wave-1
  - fetch
milestone: vault-hardening
dependencies:
  - TASK-0023
modified_files:
  - skills/inbox-fetcher/scripts/fetch_inbox.py
  - tests/test_fetch_inbox.py
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
is_pdf_url() checks the URL path suffix only. URLs like `https://example.com/download?id=42` that serve PDFs are routed to trafilatura, which returns empty content and marks the URL as failed. A HEAD request probing Content-Type: application/pdf allows correct routing without requiring a .pdf suffix.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §1.3\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 4
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 New get_content_type(url) -> str returns the Content-Type header value, or empty string on any network error
- [ ] #2 A URL without .pdf suffix whose HEAD response has Content-Type: application/pdf is routed to fetch_pdf
- [ ] #3 pdf_enabled: false blocks content-type-detected PDFs the same way as suffix-detected ones
- [ ] #4 No HEAD request is made for URLs that already match is_pdf_url()
- [ ] #5 pytest tests/test_fetch_inbox.py passes with no regressions
<!-- AC:END -->
