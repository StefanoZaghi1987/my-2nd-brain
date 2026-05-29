---
id: TASK-0080
title: 'Phase 4 – LLM Wiki Engine: Hardening & Portability'
status: Done
assignee: []
created_date: '2026-05-29 18:46'
updated_date: '2026-05-29 20:23'
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

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Phase 4 hardening pass complete. All 8 subtasks delivered on feat-hotfix branch across 13 commits (b4eb42c..ef1ea41). 165 tests pass (137 baseline → 165, +28 new).\n\n**What changed:**\n- D1/A3: Extracted shared `linkutil.py` — ended copy-paste between lint.py and find_backlinks.py, dropped dead import\n- A2: Wired `review_scope.py` into `/review` Protocol step 2 — script now actually invoked\n- A1: Created standalone `commands/split.md`, trimmed `merge.md` to MERGE-only, fixed installer deployment gap\n- B1: Added Windows `python`/`python3` callout to all 5 affected command docs\n- B2: Added `--yes/-y` non-interactive flag to `init_vault.py` bootstrap\n- B3: Fixed `chart.py` output path from next-to-template to `wiki/views/assets/`\n- E1: Added `/retry` feature — `FAILED_PATTERN`, `find_failed_entries()`, `--retry` CLI mode, `commands/retry.md`\n- C1-C4: Synced CLAUDE.md (14 checks, full slash-command list, `.claude/` path prefixes, MERGE/SPLIT split) and README.md (tree updated, linkutil.py in "Always refreshed" list)\n\n**New test files:** test_linkutil.py, test_bootstrap.py, test_chart.py, test_installer.py + extensions to test_fetch_inbox.py\n\nBranch ready for PR or merge to main.
<!-- SECTION:FINAL_SUMMARY:END -->
