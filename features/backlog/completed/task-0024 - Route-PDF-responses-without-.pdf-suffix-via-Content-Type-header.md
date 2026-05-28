---
id: TASK-0024
title: Route PDF responses without .pdf suffix via Content-Type header
status: Done
assignee: []
created_date: '2026-05-28 12:33'
updated_date: '2026-05-28 13:41'
labels:
  - wave-1
  - fetch
milestone: vault-hardening
dependencies:
  - TASK-0023
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-4
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Two additions to `skills/inbox-fetcher/scripts/fetch_inbox.py`. (1) Add `get_content_type(url, timeout=10) -> str` function after `yaml_escape()` (~line 314): does a `requests.head()` call, returns `r.headers.get("Content-Type", "")`, returns `""` on any exception. (2) In `process_vault()` routing block, add a new `elif` branch between the walled-domain check and the `fetch_html` fallback: `elif "application/pdf" in get_content_type(fetch_url):` then check `pdf_enabled` and call `fetch_pdf()` or return disabled FetchResult. Full code in plan Task 4 Steps 3-4. Note: the HEAD request must NOT fire for URLs already handled by `is_pdf_url()` (first branch). Test: `pytest tests/test_fetch_inbox.py -v`. Requires `requests-mock` installed: `pip install requests-mock`
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added `get_content_type(url, timeout=10) -> str` helper (HEAD request, returns Content-Type or "" on any exception). Added routing branch between `is_walled` and `fetch_html` fallback: `elif "application/pdf" in get_content_type(fetch_url)`. Branch applies same `pdf_enabled` guard. 3 new tests (`TestGetContentType` ×2, `TestContentTypeRouting` ×1). All 20 fetch tests pass. Commit: c739816.
<!-- SECTION:FINAL_SUMMARY:END -->
