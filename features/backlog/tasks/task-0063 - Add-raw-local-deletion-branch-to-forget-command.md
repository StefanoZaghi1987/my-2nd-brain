---
id: TASK-0063
title: Add raw/local deletion branch to /forget command
status: To Do
assignee: []
created_date: '2026-05-29 11:43'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - commands/forget.md
priority: medium
ordinal: 1200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The copy-paste-PDF/MD ingestion feature (a prior phase) added a third raw source type: `raw/local/<slug>/`. When a user runs `/forget` on a local source, `commands/forget.md` step 5 only deletes `raw/web/<slug>/` and `raw/papers/<slug>/` — it has never been updated to include `raw/local/<slug>/`. The raw folder is orphaned after forget.

CLAUDE.md's FORGET step 5 (lines 160-163) already lists all three branches correctly — this task brings `commands/forget.md` into alignment with it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/forget.md step 5 lists all three deletion branches: raw/web/<slug>/, raw/papers/<slug>/, and raw/local/<slug>/
- [ ] #2 The branch descriptions match CLAUDE.md FORGET step 5 (lines 160-163)
- [ ] #3 The step notes that this is the one case where writing to raw/ (as deletion) is permitted — consistent with existing CLAUDE.md language
<!-- AC:END -->
