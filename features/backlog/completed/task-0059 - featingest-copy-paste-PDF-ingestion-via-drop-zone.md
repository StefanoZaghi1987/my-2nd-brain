---
id: TASK-0059
title: 'feat(ingest): copy-paste PDF ingestion via drop zone'
status: Done
assignee: []
created_date: '2026-05-28 21:07'
updated_date: '2026-05-28 22:31'
labels:
  - feature
  - ingest
  - pdf
milestone: feat-ingest
dependencies: []
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable users to copy-paste PDF files into a dedicated `raw/drop/` folder and have them automatically adopted and ingested into the wiki by running `/ingest`.

**Design decisions (from spec `features/specs/2026-05-28-copy-paste-pdf-ingestion-design.md`):**
- Drop zone: `raw/drop/` (configurable via `vault.config.yml`)
- Storage: `raw/local/<slug>/` — kept separate from `raw/papers/` (URL-fetched) to preserve provenance
- New script `adopt_drop.py` handles raw-layer adoption (scripts write raw/, LLM writes wiki/)
- `fetch_method: local-pdf` distinguishes local PDFs from URL-fetched ones at every layer
- `/ingest` gains a pre-flight block that runs the script and prompts for tags/notes interactively

**Implementation plan:** `features/plans/2026-05-28-copy-paste-pdf-ingestion-plan.md`
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
**Branch:** `feat-ingest` — 16 commits, 85 tests (11 new in test_adopt_drop.py, 11 new in test_lint.py).

**What was built:** Copy-paste PDF ingestion via drop zone. Users drop PDFs into `raw/drop/` and run `/ingest` — they are automatically adopted into `raw/local/<slug>/` and ingested into the wiki. No URL required.

**New files:** `skills/inbox-fetcher/scripts/adopt_drop.py`, `tests/test_adopt_drop.py`

**Modified:** `skills/shared/vault_state.py`, `vault.config.yml`, `tests/test_vault_state.py`, `skills/vault-linter/scripts/lint.py`, `tests/test_lint.py`, `commands/ingest.md`, `CLAUDE.md`, `skills/inbox-fetcher/SKILL.md`, `skills/vault-linter/SKILL.md`, `init_vault.py`, `README.md`, `GETTING-STARTED.md`

**Key design decisions:**
- `raw/local/` is kept separate from `raw/papers/` (URL-fetched) to preserve provenance
- `fetch_method: local-pdf` is the authoritative marker at every layer (ingest, linter, refresh)
- `adopt_drop.py` is a Python script (not LLM) — preserves "scripts write raw/, LLM writes wiki/" invariant
- One documented exception to the invariant: the LLM may update `raw/local/<slug>/index.md` with user-supplied tags/notes at ingest pre-flight
- Exit codes: 0 = clean, 1 = bad vault path, 2 = partial (slug collision)
- Two new advisory lint checks: local PDF index integrity (check #14), drop zone not empty (check #15)
<!-- SECTION:FINAL_SUMMARY:END -->
