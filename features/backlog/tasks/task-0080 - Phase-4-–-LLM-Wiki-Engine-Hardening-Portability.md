---
id: TASK-0080
title: 'Phase 4 – LLM Wiki Engine: Hardening & Portability'
status: In Progress
assignee: []
created_date: '2026-05-29 18:46'
labels:
  - hardening
  - portability
milestone: Phase 4 – Hardening &amp; Portability
dependencies: []
references:
  - features/specs/2026-05-29-llm-wiki-hardening-design.md
  - features/plans/2026-05-29-llm-wiki-hardening.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Harden the LLM Wiki template/engine repo (`D:\my-2nd-brain`) across four defect classes found in a deep-dive audit. This repo generates Second Brain vaults via `init_vault.py` — it is NOT a live vault (no `wiki/`, `raw/`, etc. on disk).

**Why this matters:**
Defects cluster at two seams: (1) the template→deployment boundary — things advertised in docs that the installer never deploys (`/split`), path prefixes that break post-install, `python3` hardcoded on Windows; (2) duplicated logic — link-resolution copy-pasted in two scripts with a "keep in sync" comment, and a fully-built `review_scope.py` that nothing calls.

**Scope:**
- Class A (Correctness): fix `/split`, wire `review_scope.py`, drop dead import
- Class B (Windows portability): launcher docs, non-blocking bootstrap, chart output path
- Class C (Docs↔reality): CLAUDE.md check count, slash-command list, path prefixes, README tree
- Class D (Single source of truth): extract shared `linkutil.py`
- Class E (New feature): `/retry` for failed inbox URLs

**Spec:** `features/specs/2026-05-29-llm-wiki-hardening-design.md`
**Plan:** `features/plans/2026-05-29-llm-wiki-hardening.md` (has all exact code, test commands, file paths)

**Setup for any subtask:**
```bash
cd D:\my-2nd-brain
pip install requests trafilatura python-slugify matplotlib pytest
python -m pytest -v   # must be green before touching anything
git checkout -b feat/hardening-portability
```

**Sequential constraint:** Tasks 1 → 2 → 5 → 7 all touch `init_vault.py` and must run in that order. Tasks 3 and 6 are independent.
<!-- SECTION:DESCRIPTION:END -->
