---
id: TASK-0090
title: 'Documentation corrections: review.md, CLAUDE.md, SKILL.md, vault.config.yml'
status: Done
assignee: []
created_date: '2026-05-29 21:38'
updated_date: '2026-05-29 23:14'
labels:
  - docs
  - bugfix
milestone: m-4
dependencies: []
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
  - features/specs/2026-05-29-correctness-robustness-hardening-design.md
priority: medium
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
Four targeted doc corrections found during a deep-dive audit. No code changes — docs only.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. No tests to run (doc-only task).
Verify with `python -m pytest tests/ -v` to confirm nothing broke.

## Fix 4.8a — `commands/review.md` stale note (~line 149)
Find the line:
```
   - Contradictions → "consider `/merge` to reconcile (Phase 3, not yet available), or edit the claims manually"
```
Change to:
```
   - Contradictions → "consider `/merge` to reconcile, or edit the claims manually"
```
`/merge` is fully implemented and ships since Phase 3.

## Fix 4.8b — `CLAUDE.md` skill-dispatch table
Find the last row of the dispatch table:
```
| MERGE     | (LLM only)     | find_backlinks.py              |
```
Add immediately after:
```
| SPLIT     | (LLM only)     | find_backlinks.py              |
```
Both `/merge` and `/split` use `find_backlinks.py`; only MERGE was listed.

## Fix 4.8c — `skills/view-builder/SKILL.md` reveal references
Find step 8 in the Workflow section:
```
8. Write to `wiki/views/<slug>.md` (or `.html` for reveal).
```
Change to:
```
8. Write to `wiki/views/<slug>.md`.
```
Find the "For complex kinds (reveal decks, multi-page reports)" line (~line 61):
```
4. For complex kinds (reveal decks, multi-page reports), propose the
   outline before writing the full file.
```
Change to:
```
4. For multi-page reports, propose the outline before writing the full file.
```
Only Marp slides (`view-slides.md`) are implemented. There is no reveal.js template.

## Fix 4.8d — `vault.config.yml` enforcement-layer comments + block-list note
Update the file header comment from:
```
# Lists must use inline syntax: [a, b, c].
# Block-list syntax (- item per line) is not parsed.
```
to:
```
# List values support both inline syntax: [a, b, c]
# and block (multi-line) syntax:
#   key:
#     - a
#     - b
```
Add inline comments inside `lint:` to distinguish script-read keys from LLM-layer keys. Full replacement content is in the implementation plan (Task 10, Step 4).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 commands/review.md no longer says /merge is 'not yet available'
- [x] #2 CLAUDE.md dispatch table has a SPLIT row pointing to find_backlinks.py
- [x] #3 skills/view-builder/SKILL.md has no '.html for reveal' mention in the Workflow steps
- [x] #4 vault.config.yml header comment says block-list syntax IS supported (after task-0081 ships)
- [ ] #5 vault.config.yml lint: section has inline comments distinguishing script-enforced vs LLM-layer keys
- [ ] #6 Full pytest suite passes (no code changed)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Four doc fixes: (1) commands/review.md L149 — removed "(Phase 3, not yet available)" from /merge suggestion; (2) CLAUDE.md dispatch table — added SPLIT row (find_backlinks.py); (3) skills/view-builder/SKILL.md — reconciled all THREE reveal references (L60 "reveal decks" removed, L66 ".html for reveal" removed, L116 updated to note reveal.js not yet available); (4) vault.config.yml — replaced with enforcement-layer comments and block-list support note. CORRECTION applied: commands/view.md had two additional stale reveal references (L38, L52) not in the original plan scope — both fixed.
<!-- SECTION:FINAL_SUMMARY:END -->
