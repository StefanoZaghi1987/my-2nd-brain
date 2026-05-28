# Hot cache — where we left off

**Session:** 2026-05-28 — vault hardening brainstorm + spec + plan

## What we covered

Deep analysis of the full implementation. Identified 5 bugs, 5 structural gaps, and 4 extensions. Ran brainstorming through design + spec + implementation plan.

**Spec:** `features/specs/2026-05-28-vault-hardening-design.md`
**Plan:** `features/plans/2026-05-28-vault-hardening-plan.md`
**Branch:** `feat-brainstorming`

## 14 backlog tasks created (TASK-0021–0034)

**Wave 1 — code + tests (do sequentially within each group):**
- TASK-0021 — reflect_reminder_days config key (standalone)
- TASK-0022 → TASK-0023 → TASK-0024 — fetch pipeline: update_inbox fix, pdf_enabled, content-type
- TASK-0025 — ORPHAN_EXCEPTIONS cleanup (standalone)
- TASK-0026 → TASK-0027 — linter: check_conversations, check_index_sync

**Wave 2 — docs + config (all independent except noted):**
- TASK-0028 — SKILL.md inbox-fetcher stale text
- TASK-0029 — SKILL.md vault-linter gaps severity
- TASK-0030 — README six invariants
- TASK-0031 → TASK-0034 — /ingest command + Obsidian skeleton (both touch init-vault.sh)
- TASK-0021 → TASK-0032 — CLAUDE.md session-start + invariant #6
- TASK-0026 → TASK-0033 — /save template type:conversation

## What's open

All 14 tasks are To Do. Wave 1 tasks require pytest to pass after each. Wave 2 tasks are prose-only. Each task has implementation notes, exact file paths, and test commands — self-contained for a new conversation.

## Key decisions made

- pdf_enabled: false → walled-domain pattern (mark ⚠, leave unchecked)
- conversations linter check: advisory only, no age-based check (that belongs to /reflect)
- Obsidian: minimal skeleton only (useMarkdownLinks: false is the critical field)
- reflect_reminder_days: 14 days default, in lint: config section
- /ingest command: compact protocol sheet, not as elaborate as /forget
