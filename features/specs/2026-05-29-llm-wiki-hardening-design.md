# LLM Wiki — Hardening & Portability Design

- **Status:** Draft
- **Date:** 2026-05-29
- **Scope:** Hardening pass on the template/engine repo (no architectural change)

## Context

`D:\my-2nd-brain` is the **template/engine repo** that generates personal "Second Brain"
vaults — a concrete realization of Andrej Karpathy's LLM Wiki idea. `init_vault.py`
copies `skills/` and `commands/` into a target vault's `.claude/` and scaffolds the
runtime layer (`wiki/`, `raw/`, `.lint/`, `.review/`, `inbox.md`). The runtime dirs are
gitignored by design and absent from this repo.

A deep-dive audit found the engine is well-architected (clean `raw/`→`wiki/` separation,
14-check deterministic linter, six invariants, unattended-mode guardrails) but carries a
cluster of defects concentrated at two seams:

1. **The template→deployment boundary** — things advertised in docs that the installer
   never deploys (`/split`), path prefixes that don't resolve post-install, and
   `python3` hardcoded where Windows needs `python`.
2. **Duplicated logic** — link-resolution copy-pasted across two scripts with a manual
   "keep in sync" comment, and review-scoping logic written as prose while a tested
   `review_scope.py` sits orphaned.

None of the defects are architectural; all are fixable in place. This design hardens the
implementation across four classes the user selected — correctness, Windows portability,
docs↔reality sync, single-source-of-truth dedup — plus one new feature (`/retry`) that
properly closes the failed-URL retry loop.

### Project constraints

- Specs live in `features/specs/`; implementation plans in `features/plans/`.
- Implementation decomposes into small atomic Backlog.md tasks.
- Code comments describe WHY and never reference task/bug numbers.
- The repo uses pytest (`tests/`, 6 files); changed scripts get TDD coverage.

## Goals

1. Every advertised slash command resolves and works (fix `/split`).
2. The engine runs on stock Windows as documented (Python launcher, bootstrap, chart path).
3. CLAUDE.md matches the code (check count, command catalog, path prefixes).
4. One source of truth for link resolution and review scoping.
5. Failed inbox URLs retry with one command, not manual marker-editing.

## Non-goals

- No new output surfaces (graphs, digests, tag index) — deferred to a later cycle.
- No change to the `raw/`→`wiki/` model, the six invariants, or unattended rules.
- No proactive-dedup-at-ingest and no guided-review-fix workflow (considered, deferred).

**Verified non-issue (no work needed):** the `max_pdf_size_mb` config key is read
correctly by `fetch_inbox.py:447`; the `max_pdf_mb` name is only a local parameter. The
audit's suspected key-drift bug does not exist.

---

## For implementers — fresh-session setup

This repo is the **source/installer** (`D:\my-2nd-brain`), NOT a live vault. Runtime
directories (`wiki/`, `raw/`, `.lint/`, `.review/`) are gitignored and absent by design.

```bash
# Python dependencies required to run tests
pip install requests trafilatura python-slugify matplotlib pytest

# Verify the test suite is green before touching anything
python -m pytest -v   # from repo root

# Branch: create from feat-hotfix if not already on a feature branch
git checkout -b feat/hardening-portability
```

**init_vault.py is touched by Tasks 1, 2, 5, and 7** — these must run sequentially in
that order (all edit different lines, but sequential avoids merge conflicts in a
single-developer workflow).

**Task dependency chain:**
```
Task 1 (linkutil)
  → Task 2 (/split)
    → Task 4 (launcher docs, because merge.md is touched by Task 2)
    → Task 5 (--yes flag, sequential init_vault.py edit)
      → Task 7 (/retry, sequential init_vault.py edit)
        → Task 8 (CLAUDE.md + README sync, /split and /retry must exist first)
Task 3 (review_scope wire-up) — independent, any order
Task 6 (chart.py path) — independent, any order
```

All task details — exact code, file paths, test commands — are in the implementation
plan: `features/plans/2026-05-29-llm-wiki-hardening.md`.

---

## Design

### Class A — Correctness / broken

**A1. Fix `/split`.**
- *Problem:* CLAUDE.md advertises `/split <page> <new-A> <new-B>`, but no
  `commands/split.md` exists and `init_vault.py:COMMANDS` (lines 87-90) omits `split`, so
  the command never deploys. The SPLIT protocol prose currently lives inside
  `commands/merge.md`.
- *Decision:* create a standalone `commands/split.md` holding the SPLIT protocol (moved
  out of `merge.md`, which keeps the MERGE protocol and gains a cross-link), and add
  `"split"` to `init_vault.py:COMMANDS`.
- *Rejected alternative:* drop `/split` from CLAUDE.md and document split only as a mode
  of `/merge`. Rejected because the command is already advertised and users expect it.
- *Coupled doc fix (see C):* CLAUDE.md's MERGE section and Skill-dispatch table state the
  SPLIT protocol lives inside `merge.md` (≈lines 247-248). Update those once it moves.

**A2. Wire up `review_scope.py`.**
- *Problem:* `skills/shared/review_scope.py` is built and tested but called by nothing;
  `commands/review.md` describes the "changed since last review" scoping in prose, which
  can drift from the tested code.
- *Fix:* update `commands/review.md` to invoke `review_scope.py` for the default scope,
  following the script-invocation pattern `fetch.md` and `lint.md` already use.

**A3. Remove dead import.** `lint.py:37` imports `read_state` from `vault_state` but
never calls it. Delete it.

### Class B — Windows portability

**B1. Python launcher.**
- *Problem:* command docs hardcode `python3` (`fetch.md`, `ingest.md`, `lint.md`,
  `refresh.md`); `merge.md` uses bare `python`; `init_vault.py:439` already computes
  `py_cmd = "python3" if os.name != "nt" else "python"`. On stock Windows the documented
  `python3` invocations fail. Severity is low because the executor is an LLM that adapts
  to its OS, but the docs should be consistent and correct.
- *Decision:* normalize every command doc to platform-aware prose — e.g. "run with your
  Python 3 launcher (`python3` on macOS/Linux, `python` on Windows)". No installer change;
  source docs stay runnable; reads naturally to the agent.
- *Rejected alternative:* `init_vault.py` substitutes the resolved launcher at install
  time via a `{{PY}}` placeholder. Single source of truth, but adds a transform step to
  `install_commands()` and makes source docs non-runnable templates — more machinery than
  a low-severity, LLM-executed concern warrants.

**B2. Non-blocking bootstrap.** `init_vault.py` uses blocking `input()` (lines ~260, 380)
for git-init and CLAUDE.md-overwrite prompts, which hangs in CI/automated bootstrap. Add a
`--yes`/`--non-interactive` flag that takes safe defaults (skip overwrite, skip commit).

**B3. chart.py output path.** The `chart.py` template writes
`OUTPUT_DIR = Path(__file__).parent / "assets"`, landing PNGs next to the template instead
of `wiki/views/assets/`. Resolve output relative to the vault root, accepting the vault
root as an argument as the other scripts do.

### Class C — Docs↔reality sync (CLAUDE.md)

**C1.** Line 224 says the linter does 4 checks; it does **14**. Fix the count and short
list (or point to `vault-linter/SKILL.md` for the full enumeration).

**C2.** Add `/ingest` and `/lint` to the "Slash commands" list (lines 314-325) — their
files exist but the catalog omits them. Add `/split` (A1) and `/retry` (E1) once they land.

**C3.** Command references use bare `commands/*.md` (lines 210, 230, 238, 247), which don't
resolve post-install (they live at `.claude/commands/`). Prefix with `.claude/commands/`,
matching how skills are referenced.

**C4.** Sync the MERGE/SPLIT references after A1 moves the SPLIT protocol to its own file.

### Class D — Single source of truth

**D1. Link resolution.** `WIKILINK_RE` + `normalize_link_target` are copy-pasted in
`lint.py` and `find_backlinks.py` with a manual "keep in sync" comment.
- *Fix:* extract them into a new `skills/shared/linkutil.py` and import from both.
- *Deployment:* imports resolve via the existing `sys.path.insert(0, …/shared)` pattern
  (confirmed in `lint.py:36`) — no path change needed. The one required wiring change: add
  `"linkutil.py"` to the shared-script copy list in `init_vault.py:install_skills` (loop at
  ≈lines 363-369), or it won't ship to installed vaults.

**D2. Review scoping** is unified by A2 — `review_scope.py` becomes the only scoping path.

### Class E — New feature

**E1. `/retry` for failed inbox URLs.**
- *Problem:* once `fetch_inbox.py` appends `⚠ reason` to a failed entry, the
  unchecked-entry regex (`\s*$`) no longer matches, so retrying requires manually deleting
  the marker text.
- *Fix:*
  - `fetch_inbox.py`: the entry parser strips a trailing `⚠ …` suffix when extracting the
    URL; a `--retry` mode re-attempts only previously-failed entries (unchecked + `⚠`) and
    clears their markers on success. Already-`[x]` entries are untouched.
  - Add `commands/retry.md` and `"retry"` to `init_vault.py:COMMANDS`.
  - Add `/retry` to the CLAUDE.md slash-command list (handled in Task 8).
  - Update `README.md`: add `retry.md    /retry` to the commands/ tree; update the
    `merge.md    /merge, /split` line to split those two (merge.md now covers merge only,
    split.md now covers split) — also handled in Task 8.

---

## Testing

Per change, with TDD where a script is modified:

- **A1 / A2 / B1 / C\***: assert `init_vault.py:COMMANDS` includes `split` and `retry`; a
  bootstrap smoke test installs into a temp dir and verifies `.claude/commands/{split,
  retry}.md` and `.claude/skills/shared/linkutil.py` exist. (If the `{{PY}}` alternative is
  chosen for B1, additionally assert installed docs carry no `{{PY}}` placeholder.)
- **A3**: lint suite stays green after the import removal.
- **B2**: run `init_vault.py --yes` into a temp dir non-interactively; assert it completes
  without prompting.
- **B3**: unit-test that chart output resolves under a passed vault root.
- **D1**: the shared link-resolution module is tested once; `lint.py` and
  `find_backlinks.py` import it (no local copy). Existing `test_lint.py` and
  `test_find_backlinks.py` behavior stays green.
- **E1**: extend `test_fetch_inbox.py` — the parser extracts a URL from a `⚠`-marked line;
  `--retry` re-queues only failed entries and clears markers on success; `[x]` entries are
  left alone.

**End-to-end:** `pytest` from the repo root (all green), then `python init_vault.py --yes
<tmp>` and confirm the deployed vault has every command (including `split`, `retry`) and
`skills/shared/linkutil.py`, with correct Python-launcher guidance in the docs.

## Deliverables / process

1. This spec is committed to `features/specs/`.
2. An implementation plan goes to `features/plans/` (via the writing-plans skill).
3. Work decomposes into small atomic Backlog.md tasks (one per item A1…E1, plus test
   tasks), implemented TDD-first on a feature branch, then a PR.
