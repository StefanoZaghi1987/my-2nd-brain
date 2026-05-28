---
id: TASK-0023
title: 'Honour pdf_enabled: false in the fetch pipeline'
status: To Do
assignee: []
created_date: '2026-05-28 12:32'
updated_date: '2026-05-28 12:40'
labels:
  - wave-1
  - fetch
milestone: vault-hardening
dependencies:
  - TASK-0022
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-3
modified_files:
  - skills/inbox-fetcher/scripts/fetch_inbox.py
  - tests/test_fetch_inbox.py
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
vault.config.yml has a `fetch.pdf_enabled` key that is loaded by `process_vault()` but never consulted. When set to false, PDF URLs should behave like walled domains: marked failed with a clear reason in inbox.md and left unchecked so the user can process them manually.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §1.2\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 3
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With pdf_enabled: false, a .pdf URL produces a ⚠ annotation containing 'pdf_enabled' in inbox.md
- [ ] #2 No file is written to raw/papers/ when pdf_enabled is false
- [ ] #3 With pdf_enabled: true (the default), fetch behaviour is unchanged
- [ ] #4 pytest tests/test_fetch_inbox.py passes with no regressions
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
In `skills/inbox-fetcher/scripts/fetch_inbox.py`, find `process_vault()`. In the config-loading block at the top of the function, add: `pdf_enabled = cfg["fetch"]["pdf_enabled"]`. Then find the routing block inside the loop where `is_pdf_url(fetch_url)` is checked. Wrap the `fetch_pdf()` call with: `if not pdf_enabled: r = FetchResult(url=fetch_url, ok=False, kind="failed", reason="PDF fetch disabled (pdf_enabled: false in vault.config.yml)")` else call `fetch_pdf(...)` as before. Full replacement code is in the plan Task 3 Step 3. Test with: `pytest tests/test_fetch_inbox.py -v`
<!-- SECTION:NOTES:END -->
