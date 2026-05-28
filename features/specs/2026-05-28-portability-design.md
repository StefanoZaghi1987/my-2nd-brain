# Portability Design

**Date:** 2026-05-28
**Scope:** Four targeted improvements — semantic rename, /hot template fix,
cross-platform bootstrap script, python3 command normalisation.

---

## Context

The vault is in active use on Windows 11. Two issues affect portability
for other users (Linux, Windows+WSL, Windows without WSL):

1. `init-vault.sh` is Bash-only — not runnable on native Windows.
2. Documentation uses `python` and `python3` inconsistently — `python`
   is unreliable on Linux (may be Python 2 or absent).

Two additional bugs were found during the portability audit:

3. `fetch_inbox.py` increments a counter named `ingests_since_last_lint`
   on FETCH success, not on INGEST. The name is a lie.
4. `init-vault.sh` bootstraps `wiki/hot.md` with YAML frontmatter and
   section headers that the `/hot` command immediately overwrites on
   first run, creating a silent format drift.

---

## Item 1 — Semantic rename: `fetches_since_last_lint`

### Problem

`fetch_inbox.py` increments `ingests_since_last_lint` (and the config
key `auto_trigger_after_ingests`) on a successful fetch. INGEST is
LLM-only — there is no Python hook for it. The counter is semantically
a fetch counter used as a proxy for ingest activity. The name misleads.

### Solution

Rename everywhere. Zero behavior changes.

| Old name | New name |
|---|---|
| `ingests_since_last_lint` (state key) | `fetches_since_last_lint` |
| `auto_trigger_after_ingests` (config key) | `auto_trigger_after_fetches` |

**Files changed:**

| File | What changes |
|---|---|
| `skills/shared/vault_state.py` | `_DEFAULTS`: both key names |
| `skills/inbox-fetcher/scripts/fetch_inbox.py` | `read_state` / `write_state` call |
| `vault.config.yml` | config key name |
| `CLAUDE.md` | session-start auto-lint condition text |
| `commands/lint.md` | auto-trigger condition text |
| `tests/test_vault_state.py` | all `ingests_since_last_lint` references |

**State migration:** Existing `.lint/state.yaml` files have the old key.
After rename, `read_state()` returns nothing for the new key — counter
silently resets to 0. At most one missed auto-lint trigger. No migration
script needed.

---

## Item 2 — `/hot` template fix

### Problem

`init-vault.sh` bootstraps `wiki/hot.md` with:

```
---
type: page
created: INIT
updated: INIT
tags: [hot-cache]
---
# Hot Cache
## Recent sessions
## Open threads
```

The `/hot` command (commands/hot.md) replaces the entire file with:

```
## [YYYY-MM-DD]
[5-10 lines prose]
```

After first `/hot` run: frontmatter gone, H1 gone, both sections gone.
`type: page` is also a semantic lie — hot.md is a session cache, not a
wiki page.

### Solution

Remove frontmatter and structural headers from the initial `wiki/hot.md`
in `init-vault.sh`. The initial content should match the `/hot` output
format exactly:

```markdown
## [INIT]

Vault just bootstrapped. No sessions yet.
```

`wiki/hot.md` is in `ORPHAN_EXCEPTIONS` — the linter already skips
metadata checks for it. No downstream impact.

**Files changed:** `init-vault.sh` only (the `cat > wiki/hot.md` heredoc).

---

## Item 3 — `init_vault.py`: cross-platform bootstrap

### Problem

`init-vault.sh` uses Bash-only constructs (`pipefail`, `${BASH_SOURCE[0]}`,
`tput`, `ln -s`, `chmod +x`, `read -r -p`) and cannot run on native
Windows. Python is already a hard dependency of the vault, so a Python
bootstrap requires nothing new from the user.

### Solution

New file `init_vault.py` at the repo root, parallel to `init-vault.sh`.
`init-vault.sh` is kept unchanged (existing Unix users unaffected).

**Interface (identical to `.sh`):**
```
python3 init_vault.py                  # creates ./second-brain-vault
python3 init_vault.py /path/to/vault   # explicit path
python3 init_vault.py --here           # current directory
python3 init_vault.py --help
```

**Platform decisions:**

| Concern | Approach |
|---|---|
| ANSI colors | Direct escape codes; disabled when `not sys.stdout.isatty()` |
| Symlinks | `os.symlink()` in `try/except (OSError, NotImplementedError, PermissionError)` → fallback `shutil.copy2()`. No warning — copy is a valid fallback. |
| `chmod +x` | `os.chmod(path, 0o755)` guarded by `if os.name != "nt"` |
| Python dep check | `subprocess.run([sys.executable, "-c", "import pkg"])` — uses the running interpreter, never guesses a command name |
| Git identity | Before committing: check `git config user.name` and `git config user.email`. If either empty, skip commit with a warning. |
| "Next steps" python cmd | `"python3"` on Unix (`os.name != "nt"`), `"python"` on Windows |

**Behaviour parity with `init-vault.sh`:**

- Idempotent (safe to re-run)
- Prompts before overwriting `CLAUDE.md`
- Skips `vault.config.yml`, `inbox.md`, wiki files if they already exist
- Always refreshes skills, commands, `vault_state.py`
- Optional `git init`

**Files created/changed:**

| File | Action |
|---|---|
| `init_vault.py` | New file (~250 lines, stdlib only) |
| `README.md` | Add `python3 init_vault.py` as Windows / universal path; keep `.sh` as Unix path |
| `GETTING-STARTED.md` | Mention `init_vault.py` in Day 1 bootstrap step |

---

## Item 4 — `python3` vs `python` normalisation

### Problem

Documentation is inconsistent:
- `init-vault.sh` checks `command -v python3` (correct for Unix)
- `commands/fetch.md`, `commands/lint.md`, `commands/refresh.md` use `python` (may invoke Python 2 on Linux)
- `skills/inbox-fetcher/SKILL.md` mixes `python` and `python3` within the same file
- `skills/vault-linter/SKILL.md` uses `python`

### Solution

**Rule:** `python3` is the canonical command in all documentation.
**Windows note:** one sentence in README.md and GETTING-STARTED.md:
> On Windows, use `python` if `python3` is not recognised.

`init_vault.py` handles this automatically in its "Next steps" output
by printing the platform-appropriate command.

**Files changed:**

| File | Change |
|---|---|
| `commands/fetch.md` | `python` → `python3` |
| `commands/lint.md` | `python` → `python3` (×2); also rename auto-trigger key text (Item 1 overlap — same task) |
| `commands/refresh.md` | `python` → `python3` |
| `skills/inbox-fetcher/SKILL.md` | `python` → `python3` (all occurrences) |
| `skills/vault-linter/SKILL.md` | `python` → `python3` (all occurrences) |
| `README.md` | `python3` canonical + Windows note (combined with Item 3 README task) |
| `GETTING-STARTED.md` | `python3` canonical + Windows note (combined with Item 3 GETTING-STARTED task) |

---

## Invariants — unchanged

All six vault invariants are unaffected. No changes to `raw/`, `wiki/`,
or any LLM-facing operation protocol. The semantic rename (Item 1) is
a name correction with no behavior change. The `/hot` fix (Item 2) is
a template alignment with no protocol change.

---

## Non-goals

- `init-vault.ps1` (PowerShell parallel script) — not needed; Python is
  already required and `init_vault.py` covers the Windows use case.
- Automated state migration for the counter rename — one missed lint
  trigger is acceptable, no migration script needed.
- Deprecating `init-vault.sh` — kept as-is for existing Unix users.
