# Hot cache — where we left off

**Session:** 2026-05-28 — vault hardening implementation complete

## What we covered

Full implementation of the vault-hardening cycle (TASK-0021–0034). All 14 tasks
implemented, reviewed (spec + quality), and committed on `feat-hardening`. Branch
is clean and ready to squash-merge into main.

**Spec:** `features/specs/2026-05-28-vault-hardening-design.md`
**Plan:** `features/plans/2026-05-28-vault-hardening-plan.md`
**Branch:** `feat-hardening` (16 commits, 51/51 tests passing)

## What was delivered

**Wave 1 — code + tests:**
- TASK-0021 — `reflect_reminder_days: 14` config key in vault_state.py + vault.config.yml
- TASK-0022 — `update_inbox` sub-bullet orphan fix (while-loop with look-ahead)
- TASK-0023 — `pdf_enabled: false` now enforced in fetch pipeline
- TASK-0024 — `get_content_type()` helper + Content-Type PDF routing for suffix-less URLs
- TASK-0025 — Dead `ORPHAN_EXCEPTIONS` entries removed (`"index.md"`, `"log.md"`)
- TASK-0026 — `check_conversations`: advisory finding for missing `type: conversation`
- TASK-0027 — `check_index_sync`: advisory finding when source absent from index.md

**Wave 2 — docs + config:**
- TASK-0028 — inbox-fetcher SKILL.md: sub-bullet description corrected
- TASK-0029 — vault-linter SKILL.md: gaps moved from Important → Advisory
- TASK-0030 — README.md: Six invariants (was Five), 6th added
- TASK-0031 — `commands/ingest.md` created, registered in init-vault.sh loop
- TASK-0032 — CLAUDE.md: `## Session start` section + invariant #6 sharpened
- TASK-0033 — `commands/save.md`: `type: conversation` + `promoted_to: []` in template
- TASK-0034 — init-vault.sh: `.obsidian/` dir + `app.json` with `useMarkdownLinks: false`

**Post-cycle doc sync:**
- CLAUDE.md FORGET step 6: bare `index.md`/`log.md` → full `wiki/` paths
- README.md: `ingest.md` added to commands listing
- GETTING-STARTED.md: 8 slash commands, 6 rules, /ingest in operations table,
  Obsidian note updated

## What's open

Nothing from this cycle. All TASK-0021–0034 marked Done in backlog.

Next natural steps (not tasked):
- First real use of `/ingest` command after a fetch run — verify the new
  protocol sheet is followed correctly by the agent
- Run `/lint` to exercise `check_conversations` and `check_index_sync` on the
  live vault for the first time
- Consider running `init-vault.sh --here` to install the new `/ingest` command
  and Obsidian skeleton into the live vault
