# LLM Wiki — Correctness Fixes + Documentation Restructure

**Date:** 2026-05-31  
**Branch:** feat-hotfix  
**Scope:** Correctness gaps (Tier 1–2) + documentation restructure. New features deferred.

---

## Codebase orientation (for fresh-conversation start)

**Repo type:** Template/installer, NOT a live vault. `init_vault.py` mints deployed
vaults into `./second-brain-vault/` (gitignored). This repo has no `raw/`, `wiki/`,
or `inbox.md` — those appear only in deployed vaults.

**Key files and exact locations:**

| File | Purpose | Key section for this work |
|---|---|---|
| `init_vault.py` | Cross-platform vault bootstrapper | `install_skills()` lines 338–382; `print_done()` line 472 |
| `skills/shared/vault_state.py` | Config loader + `_DEFAULTS` | `_DEFAULTS` dict lines 42–75 |
| `vault.config.yml` | Per-vault config template | `ingest:` block lines 38–40 (end of file) |
| `tests/test_installer.py` | Installer tests (currently 4 simple path assertions) | — |
| `CLAUDE.md` | Agent contract (442 lines) | `## Six invariants` line 42; `## Twelve operations` line 144; `## Session start` line 350; `## Skill dispatch` table line 317; Backlog block line 414 |
| `GETTING-STARTED.md` | Human onboarding (260 lines) | `## Twelve operations` line 75; `## Sixteen slash commands` line 97; `## Six rules` line 206 |
| `README.md` | GitHub landing / install (212 lines) | `## Design principles` line 127; Quick start ends line 110 |

**Convention check — `_DEFAULTS` vs LLM-layer-only keys:**
`vault_state.py::_DEFAULTS` includes ALL config sections including `ingest:` and
lint's LLM-layer-only keys. This confirms: `review:` must be added to `_DEFAULTS`
(not config-only) to match the existing convention.

**`install_skills` current structure (lines 338–382 verbatim sketch):**
```python
for skill_name, py_scripts in [
    ("inbox-fetcher", ["scripts/fetch_inbox.py", "scripts/adopt_drop.py"]),
    ("vault-linter",  ["scripts/lint.py"]),
    ("view-builder",  []),
]:
    ...copy SKILL.md + iterate py_scripts...

_SHARED_SCRIPTS = ["vault_state.py", "yamlmini.py", "console.py",
                   "review_scope.py", "find_backlinks.py", "linkutil.py"]
for _script in _SHARED_SCRIPTS:
    ...copy each to shared/...
```
The hardcoded lists are what must be replaced with auto-discovery.

---

## Background

A full audit of the engine (3 parallel exploration passes) confirmed: 98 completed
backlog tasks, 11 pytest modules, every advertised command/skill/script backed by real
code. The engine is mature. Two categories of real issues surfaced:

1. **Correctness gaps** — things the system claims to do that it doesn't fully do.
2. **Documentation drift** — duplicated, counted lists living in three files allowed
   them to diverge (the "six invariants" is the primary symptom).

The repo is a **template/installer**, not a live vault. `init_vault.py` mints vaults
into a gitignored target dir; this is why CLAUDE.md's `.claude/...` paths resolve
post-install, not in-repo. That fact is currently invisible in the docs.

---

## Goals / Non-goals

**In scope**
- Fix Tier-1 correctness gaps: `compass.md` referenced but never scaffolded; (preventive) installer script-list robustness.
- Fix Tier-2 config/doc drift: `review.max_faithfulness_pages` undocumented in config; operation/command count mismatch in headings.
- Restructure the three docs around a single-source-of-truth model to permanently stop drift.
- Reconcile the invariants into one canonical, tiered set in CLAUDE.md.
- Regression test coverage for any installer changes.

**Out of scope (deferred)**
- reveal.js slides template (documented as "not yet available")
- Real chart authoring workflow (chart.py is an intentional per-view stub)
- A formal `/query` slash command
- Tier-3 cosmetics (applied opportunistically only in files already open for A/B edits)

---

## Part A — Correctness fixes

### A1. `compass.md` — soften the contract, don't fabricate a stub

**Problem:** `CLAUDE.md` session-start step 3 tells the agent to read `wiki/compass.md`;
`init_vault.py`'s closing banner repeats this. But the installer never seeds the file —
it is created by `/reflect` at runtime. A fresh vault has no `compass.md`.

**Why not a stub:** A stub would contain fake reflection prose, violating the vault's
"every claim cites a source" ethos.

**Fix:**
- `CLAUDE.md` session-start §3: make the compass read explicitly conditional:
  *"If `wiki/compass.md` exists, read its `updated` field and check the
  `reflect_reminder_days` threshold. If absent or the file doesn't exist yet, suggest
  running `/reflect` to create it."*
- `init_vault.py` closing banner: replace any instruction to read `compass.md` with
  a pointer to run `/reflect` after first ingest.

**Files:** `CLAUDE.md`, `init_vault.py`

---

### A2. Installer's hardcoded script list — auto-discover (PREVENTIVE)

**Severity:** Not a current bug — every existing script is in the hardcoded list.
This is future-proofing. YAGNI note: the user may opt out; implement only if it fits
the effort budget.

**Problem:** `init_vault.py::install_skills` enumerates exact script filenames to copy.
Add a new `.py` under `skills/` without updating the list → silently omitted (`warn`
only). This is the most likely future breakage point.

**Fix:** Replace the hardcoded filename list with auto-discovery:
- For each skill's `scripts/` dir and `skills/shared/`: copy every `.py` found.
- **Defensive exclusions:** skip `__pycache__/`, `test_*.py`, `*_test.py`, and any
  `.py` not directly under `scripts/` (i.e., no recursive sub-dir sweeping).
- Keep a `warn` if a skill has a `scripts/` dir but it's unexpectedly empty.
- Preserve the existing target layout exactly.

**Test:** Add a fixture-based case in `tests/test_installer.py` that:
1. Writes a dummy `skills/<skill>/scripts/_probe.py` into a temp skill dir.
2. Runs `install_skills` against a temp target.
3. Asserts `_probe.py` was installed at `.claude/skills/<skill>/scripts/_probe.py`.
4. Also asserts a `test_something.py` sibling was NOT installed.

**Files:** `init_vault.py` (`install_skills`), `tests/test_installer.py`

---

### A3. `review.max_faithfulness_pages` — document in config

**Problem:** `commands/review.md` reads `review.max_faithfulness_pages` (defaulting to
10 if absent). There is no `review:` section in `vault.config.yml` or `_DEFAULTS`.
The behavior is graceful but the knob is undocumented and invisible to a user
customizing the config.

**Fix:** Add a `review:` block to `vault.config.yml`, annotated as LLM-layer-only
(matching the file's existing convention):

```yaml
# --- Review (LLM-layer only; not read by any script) ---
review:
  # Max pages to run the claim-faithfulness check against per /review run.
  # Increase for thorough audits; decrease to control token spend.
  max_faithfulness_pages: 10
```

Check `vault_state.py::_DEFAULTS`: if other LLM-layer keys (ingest/auto-trigger)
are NOT mirrored there, leave `review` config-only for consistency. If they are,
mirror it.

**Files:** `vault.config.yml`, verify `skills/shared/vault_state.py`

---

### A4. Operation / command count mismatch — drop hardcoded counts from headings

**Problem:** "Twelve operations" labels 13 verbs (MERGE/SPLIT collapsed into one
numbered row); 12 operations vs 16 commands is never reconciled in the docs. The
count is a recurring lie waiting to drift again.

**Fix:**
- Rename the `## Twelve operations` heading → `## Operations` everywhere (CLAUDE.md,
  GETTING-STARTED.md). Same for any "Sixteen slash commands" heading → "Slash commands."
- Add one reconciliation sentence to GETTING-STARTED under the operations table:
  *"Four commands — `/retry`, `/save`, `/hot`, `/playwright-fetch` — are utilities
  and sub-steps rather than top-level operations; that's why the slash-command count
  is higher than the operation count."*

**Files:** `CLAUDE.md`, `GETTING-STARTED.md`

---

## Part B — Documentation restructure

### Ownership model

| Content | Canonical owner | Others do… |
|---|---|---|
| Invariants / operating rules (full) | **CLAUDE.md** | README: brief un-numbered teaser + "see CLAUDE.md". GETTING-STARTED: short narrative, no re-enumeration. |
| Operation protocols | **CLAUDE.md** | GETTING-STARTED: teaches core flow, links for full list. |
| Full command list | **CLAUDE.md** "Slash commands" | GETTING-STARTED: teaches key ones, links for complete reference. |
| Install / bootstrap steps | **README** | GETTING-STARTED Day-1 links to README. |
| Teaching content (first week/month, FAQ) | **GETTING-STARTED** | — |
| Template-vs-instance explainer | **README** (new section) | One-line note in CLAUDE.md. |

**Why keep three docs:** README is the GitHub front door (must be self-contained for
evaluators); GETTING-STARTED is post-install teaching. Different audiences, different
moments.

---

### B1. Reconcile invariants — tiered split

**Root cause of drift:** "Six invariants" is a *claim* — a hardcoded count in a
heading. The moment any doc adds or reorganizes an idea, the count diverges. The fix
is not finding the "right six" — it's **removing the hardcoded count** and giving the
ideas a semantic home that makes re-categorization explicit.

**Canonical set in CLAUDE.md** (replaces current `## Six invariants — never break these`):

```
## Invariants and operating rules

### Hard invariants — never break these
These are integrity guarantees. Violating them corrupts the vault's truthfulness.

1. **Never write to `raw/`.** … (preserve existing carve-outs)
2. **Every claim cites a source.** …
3. **Paraphrase, don't copy.** …

### Operating rules
These govern how the agent works. They are firm defaults, not absolute constraints,
but deviating requires an explicit user instruction.

- **User curates, agent maintains.** …
- **Touch ≤15 files per operation.** …
- **Update `wiki/index.md` and `wiki/log.md`** after any writing operation. …
- **`shareable: true` views are frozen.** …
```

Note: this explicitly reunites the rule that existed in README/GETTING-STARTED
("shareable views frozen") but was absent from CLAUDE.md, and the rule that existed
in CLAUDE.md (#6: "update index/log") but was absent from the user-facing docs.

**Fallback:** If the tiered diff feels too heavy during implementation, downshift to
"promote to seven flat invariants + drop all hardcoded counts" — same drift-fix
benefit, less prose churn.

**README:** Replace `## Design principles` / `## Six invariants` with a brief
**unnumbered** list (one line per principle), ending with:
*"The authoritative set, with operating rules distinguished from hard invariants, is
in [CLAUDE.md — Invariants and operating rules](CLAUDE.md)."*

**GETTING-STARTED:** Remove the numbered "Six rules the agent follows" list entirely.
Replace with a 2-3 sentence narrative pointing to CLAUDE.md.

**Files:** `CLAUDE.md`, `README.md`, `GETTING-STARTED.md`

---

### B2. De-duplicate command list and framing

**Command list:** GETTING-STARTED currently re-lists all 16 commands verbatim —
duplicating CLAUDE.md's "Slash commands" section. Replace with a curated "core
commands" list covering the first-week workflow (~7 commands), followed by:
*"The complete reference for all commands is in [CLAUDE.md — Slash commands](CLAUDE.md)."*

**Karpathy framing:** The same intro paragraph (Karpathy gist, "you curate / agent
compiles") appears near-verbatim in both README and GETTING-STARTED. Keep it in
README (the entry point); GETTING-STARTED starts from the concept, not the origin
story, and links to README for context.

**Files:** `GETTING-STARTED.md`, `README.md`

---

### B3. Add the "template, not a vault" explainer

**New README section** (after "Quick start", before or merged with "The core idea"):

```
## This repo is the template, not a vault

Cloning this repo gives you the engine. Live content — `raw/`, `wiki/`, `inbox.md`
— exists only in a *deployed vault* created by `init_vault.py` (default target:
`./second-brain-vault/`, gitignored). The `.claude/...` paths that appear throughout
`CLAUDE.md` resolve post-install, not here. `AGENTS.md` is generated at bootstrap
(a copy of `CLAUDE.md`); it is not committed to this repo.
```

**One-line note in CLAUDE.md** (top of "Vault structure" §):
*"Paths beginning with `.claude/` refer to the deployed vault layout after
`init_vault.py` installs commands and skills there, not to this template repo."*

**Files:** `README.md`, `CLAUDE.md`

---

### B4. CLAUDE.md hygiene

**Skill-dispatch table:** correct loose script shorthand to full repo-relative paths:
- `scripts/fetch_inbox.py` → `skills/inbox-fetcher/scripts/fetch_inbox.py`
- `scripts/lint.py` → `skills/vault-linter/scripts/lint.py`
- `find_backlinks.py` → `skills/shared/find_backlinks.py`

**Backlog MCP block:** leave content as-is; add a comment separator:
`<!-- ───── Tooling config below — not part of the vault contract ───── -->`

**"Operations" count heading (A4):** already covered above.

**Files:** `CLAUDE.md`

---

### Part C — Tier-3 polish (opportunistic only)

Apply only if the file is already open for an A/B edit:
- `skills/inbox-fetcher/SKILL.md`: add `adopt_drop.py` to the directory tree diagram.
- `chart.py`: no change needed (existing `# --- Customise below ---` banner is adequate).

---

## Files to modify

| File | Changes |
|---|---|
| `CLAUDE.md` | Invariants → tiered; session-start compass conditional; "Operations" heading; dispatch-table paths; template note; tooling separator |
| `README.md` | Template-vs-instance section; un-numbered principles teaser → CLAUDE.md; framing de-dup; AGENTS.md note |
| `GETTING-STARTED.md` | Drop numbered invariant re-list; drop full command re-list (link); operations-vs-commands sentence; framing de-dup |
| `vault.config.yml` | Add `review:` block |
| `init_vault.py` | A2 auto-discover; A1 banner fix |
| `skills/shared/vault_state.py` | Mirror `review` default only if convention requires |
| `tests/test_installer.py` | A2 regression test |
| `skills/inbox-fetcher/SKILL.md` | (Tier-3, opportunistic) |

Total: 7–8 files. Well within the 15-file touch-budget.

---

## Verification checklist

1. **A2 regression test:** `pytest tests/test_installer.py` — new case passes;
   existing cases unbroken.
2. **Full suite:** `pytest` — all 11 modules green.
3. **Fresh-vault smoke (A1):** `python init_vault.py <temp-dir>` — banner does not
   instruct reading a non-existent `compass.md`; `wiki/{index,log,hot}.md` exist;
   `compass.md` absent (correct).
4. **Config parse (A3):** `vault_state.load_config` in a temp dir with the updated
   `vault.config.yml`; confirm `review.max_faithfulness_pages` resolves to 10.
5. **Doc consistency:** grep all three docs for "six"/"twelve"/"sixteen" + count claims;
   confirm exactly one authoritative numbered/tiered list and all others defer by link.
6. **Link check:** no new broken `[[...]]` or markdown links introduced.
7. **Anti-hollowing read:** read each doc as its target audience; confirm each stands
   alone and was not gutted into pure cross-references.

---

## Deferred / future work

- reveal.js slides template (view-builder SKILL.md documents: "not yet available")
- Real chart authoring workflow (chart.py is designed as a per-view stub)
- Formal `/query` slash command
- `review.md`'s `max_faithfulness_pages` key: confirm `_DEFAULTS` consistency is resolved
  in A3 (tracked here in case it surfaces a deeper config-layer question)
