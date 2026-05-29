---
id: TASK-0066
title: Fix stale flat-PDF documentation in fetch_inbox.py and SKILL.md
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
  - skills/inbox-fetcher/SKILL.md
priority: low
ordinal: 1500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two documentation strings still describe the old flat-file PDF layout that was superseded when the copy-paste-PDF ingestion phase introduced a folder-per-source layout:

- `skills/inbox-fetcher/scripts/fetch_inbox.py` module docstring (line 12): says PDFs go to `raw/papers/<slug>.pdf`
- `skills/inbox-fetcher/SKILL.md` line 93: says "download as-is to `raw/papers/<slug>.pdf`"

The `fetch_pdf()` function docstring (line 173) already correctly says `raw/papers/<slug>/` with a companion `index.md`. The linter's `check_pdf_index` flags the flat layout as legacy — meaning these docs describe exactly what the linter considers wrong.

Update both strings to match the current folder layout: `raw/papers/<slug>/paper.pdf` + `index.md`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 fetch_inbox.py module docstring describes PDFs going to raw/papers/<slug>/ (folder) not raw/papers/<slug>.pdf (flat file)
- [ ] #2 SKILL.md PDF detection step describes raw/papers/<slug>/paper.pdf + index.md
- [ ] #3 Grep for 'raw/papers/<slug>.pdf' in fetch_inbox.py and SKILL.md returns zero matches
<!-- AC:END -->
