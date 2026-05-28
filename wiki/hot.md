# Hot cache — where we left off

**Session:** 2026-05-28 — vault improvements Wave 1 + Wave A

## What we covered

Implementing the vault improvements plan (`features/plans/2026-05-28-vault-improvements-plan.md`).

Wave 1 (foundation) was already complete from a prior session.

This session completed **Wave A** (pure file creation):
- `commands/lint.md` — TASK-0006 ✅
- `commands/promote.md` — TASK-0013 ✅ (step ordering fixed: source file created before citations written)
- `commands/refresh.md` — TASK-0014 ✅ (unattended mode clarified: requires interactive; log destination fixed to log.md)
- `skills/view-builder/templates/view-concept-map.md` — `<details>` fallback block added (TASK-0017 partial, commit 150eb03)

All Wave A commits on branch `feat-foundation`. Tests: 36/36 pass.

## What's open

Remaining tasks in order of execution waves:

- **Wave B** (sequential, `fetch_inbox.py`): TASK-0009 → TASK-0010
- **Wave C** (single subagent, `CLAUDE.md`): TASK-0011 + TASK-0016 merged
- **Wave D** (single subagent, SKILL.md files): TASK-0017 (sync rule) + TASK-0018
- **Wave E** (sequential, `init-vault.sh`): TASK-0015 → TASK-0019
- TASK-0020 auto-satisfied by Wave C

## What to pick up next

Start with Wave B. Read `skills/inbox-fetcher/scripts/fetch_inbox.py` (current state is post-Task-4 migration — vault_state imported, tags/note on InboxEntry, but `fetch_html` and `fetch_pdf` don't yet accept tags/note params and fetch_pdf still writes a flat .pdf file).

The detailed plan has exact code for each task. Tests go in `tests/test_fetch_inbox.py`.

After Wave B passes pytest, run Waves C, D, E, then final smoke test:
```bash
bash init-vault.sh /tmp/test-vault-final && ls /tmp/test-vault-final/.claude/commands/
```
Expected: `forget.md lint.md promote.md reflect.md refresh.md save.md view.md`
