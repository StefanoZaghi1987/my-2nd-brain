# Ingest Depth & Coverage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix shallow wiki pages by (1) adding an adaptive page/source structure schema to `CLAUDE.md`, (2) replacing the fixed page-window PDF read in `/ingest` with a map-then-read protocol, (3) creating a new `/expand <page>` command that reads sources in full and appends a `## Deep dive` section on demand.

**Architecture:** Pure prose/Markdown changes — no Python. Six files modified or created. `CLAUDE.md` gains a new schema section and five EXPAND registration points. `commands/ingest.md` gets the map-then-read protocol. `commands/expand.md` is created from scratch, following the `/refresh` command anatomy. `commands/review.md` gains a one-line suggestion wiring thin-page detection to `/expand`. `README.md` and `GETTING-STARTED.md` are updated to list the new command.

**Tech Stack:** Markdown prose. Verification via `skills/vault-linter/scripts/lint.py` on a scratch vault.

**Spec:** `features/specs/2026-05-30-ingest-depth-coverage-design.md`

---

## Repo context (read this first in a fresh session)

`D:\my-2nd-brain` is the **template/engine repo** — it is NOT a live vault. It
contains the CLAUDE.md contract, command files, skills, and scripts that get installed
into a new vault when `python init_vault.py <target-dir>` is run. There is no `wiki/`,
`raw/`, or `inbox.md` in this directory. All changes here affect EVERY future vault
bootstrapped from this template.

All changes in this plan are to files in `D:\my-2nd-brain` (the template repo):
- `CLAUDE.md` — the LLM operating contract installed into every vault
- `commands/*.md` — slash command protocol files installed into every vault
- `README.md`, `GETTING-STARTED.md` — documentation for this template repo

To create a scratch vault for Task 7 verification:
```
python init_vault.py C:\temp\scratch-vault
```
(Use `python`, not `python3`, on Windows.)

---

## File Map

| File | Action | Task |
|------|--------|------|
| `CLAUDE.md` | Modify — add page/source structure schema section | Task 1 |
| `CLAUDE.md` | Modify — add EXPAND op, slash command, dispatch row, hot trigger, unattended guard, update operation count | Task 2 |
| `commands/ingest.md` | Modify — map-then-read for web articles, PDFs, local-md; reframe guard | Task 3 |
| `commands/expand.md` | **Create** — new command following `/refresh` anatomy | Task 4 |
| `commands/review.md` | Modify — step 9 suggestion: thin → `/expand` | Task 5 |
| `README.md` | Modify — add expand.md to command file tree | Task 6 |
| `GETTING-STARTED.md` | Modify — add EXPAND to operations table and command list | Task 6 |

---

## Task 1 — Add page & source structure schema to `CLAUDE.md`

**Files:** Modify `CLAUDE.md`

**Context:** The Frontmatter section (lines 62–95) ends with the `shareable: false`
explanation and a `---` separator. "## Eleven operations" immediately follows. The new
schema section goes between those two, giving the LLM a generation contract for every
page and source body — the missing equivalent of the 7 view-builder templates.

- [ ] **Step 1: Open CLAUDE.md and locate the insertion point**

  Find the block:
  ```
  When `shareable: true`, treat the view as frozen — don't silently
  update it. When `shareable: false` (default), the view evolves.

  ---

  ## Eleven operations
  ```

- [ ] **Step 2: Insert the page & source structure section**

  Replace the block above with:

  ```markdown
  When `shareable: true`, treat the view as frozen — don't silently
  update it. When `shareable: false` (default), the view evolves.

  ---

  ## Page & source structure

  Every `wiki/sources/<slug>.md` and `wiki/pages/<slug>.md` body follows an adaptive
  structure — cover a section only when the source actually supports it; skip rather
  than pad with "none discussed."

  **`wiki/sources/<slug>.md`** body (after frontmatter):

      <One-line capsule: author, venue, type, date.>

      ## Summary
      2–5 paragraphs covering the core argument or contribution, in your own words.
      If a `note` directive was supplied, address it explicitly here — not just
      acknowledge it.

      ## Key points
      - <Substantive claim — must be traceable to the raw source>
      - <…>

      ## Connections
      - [[wiki/pages/<concept>]] — <one phrase: how this source relates>

  **`wiki/pages/<slug>.md`** body (after frontmatter):

      <One-line definition of the concept.>

      ## Overview
      3–6 sentences: what it is, why it matters, key variants.
      This section is what incoming links resolve to — keep it scannable.

      ## Key dimensions
      One H3 (###) subsection per facet the available sources support.
      Each facet: 1–3 sentences + inline citation to [[wiki/sources/slug]].

      ## Connections
      - [[wiki/pages/<related>]] — <relationship in one phrase>

      ## Sources
      - [[wiki/sources/<slug>]] — <one phrase: what this source contributes>

      ## Deep dive
      Added only by /expand. Absent on standard ingested pages.
      Full treatment: methodology, evidence, nuance, limitations.

  ---

  ## Eleven operations
  ```

- [ ] **Step 3: Verify the edit**

  Read `CLAUDE.md`. Confirm:
  - The new "Page & source structure" section appears between the Frontmatter `---`
    separator and "## Eleven operations".
  - Both `wiki/sources/` and `wiki/pages/` templates are present with indented bodies.
  - No other content was changed.

- [ ] **Step 4: Commit**

  ```
  git add CLAUDE.md
  git commit -m "docs(claude): add adaptive page/source structure schema"
  ```

---

## Task 2 — Register EXPAND throughout `CLAUDE.md`

**Files:** Modify `CLAUDE.md`

**Depends on:** Task 1 must be complete first. Task 1 keeps the text `## Eleven operations`
in place; Task 2 renames it to `## Twelve operations`. If Task 2 runs before Task 1,
the "Eleven operations" string won't exist and steps will fail.

**Context:** Six registration points in CLAUDE.md. Doing them all in one task keeps
the "Twelve operations" count, the dispatch table, and the slash-command list in sync.

- [ ] **Step 1: Update the operations count header**

  Find:
  ```
  ## Eleven operations
  ```
  Replace with:
  ```
  ## Twelve operations
  ```

- [ ] **Step 2: Add the EXPAND operation entry**

  Find this block in the operations list:
  ```
  ### REFRESH
  User says "refresh source X", "the article changed", or runs `/refresh <source>` →
  re-fetch a source and re-ingest it, preserving the citation graph. Flags pages
  that cite the source with `needs-review` frontmatter tag. See `.claude/commands/refresh.md`
  for the full protocol.

  ### MERGE
  ```

  Replace with:
  ```
  ### REFRESH
  User says "refresh source X", "the article changed", or runs `/refresh <source>` →
  re-fetch a source and re-ingest it, preserving the citation graph. Flags pages
  that cite the source with `needs-review` frontmatter tag. See `.claude/commands/refresh.md`
  for the full protocol.

  ### EXPAND
  User says "expand this page", "deepen page X", or runs `/expand <page>` →
  read the cited source(s) in full and append a `## Deep dive` section for
  comprehensive treatment. Leaves `## Overview` and `## Key dimensions` intact —
  they remain the link target. See `.claude/commands/expand.md` for the full protocol.

  Not available unattended.

  ### MERGE
  ```

- [ ] **Step 3: Add EXPAND to the Skill dispatch table**

  Find:
  ```
  | REFRESH   | (LLM only)     | —                              |
  | FORGET    | (LLM only)     | —                              |
  ```

  Replace with:
  ```
  | REFRESH   | (LLM only)     | —                              |
  | EXPAND    | (LLM only)     | —                              |
  | FORGET    | (LLM only)     | —                              |
  ```

- [ ] **Step 4: Add "expand" to the /hot trigger list**

  Find:
  ```
  "Written to" means any ingest, promote, view, reflect, review,
  forget, refresh, or merge that produced file changes — not queries.
  ```

  Replace with:
  ```
  "Written to" means any ingest, promote, view, reflect, review,
  forget, refresh, expand, or merge that produced file changes — not queries.
  ```

- [ ] **Step 5: Add /expand to the Unattended CANNOT list**

  Find:
  ```
  You CANNOT: merge or split pages, ingest, forget, create views, modify `wiki/pages/`,
  delete anything from `raw/` or `wiki/sources/`, apply any structural
  change.
  ```

  Replace with:
  ```
  You CANNOT: merge or split pages, expand, ingest, forget, create views, modify `wiki/pages/`,
  delete anything from `raw/` or `wiki/sources/`, apply any structural
  change.
  ```

- [ ] **Step 6: Add /expand to the Slash commands list**

  Find:
  ```
  - `/refresh <source>` — re-fetch and re-ingest a changed source
  - `/fetch` — process the URL queue in inbox.md (see FETCH above)
  ```

  Replace with:
  ```
  - `/refresh <source>` — re-fetch and re-ingest a changed source
  - `/expand <page>` — deepen an existing page from the full source (see EXPAND above)
  - `/fetch` — process the URL queue in inbox.md (see FETCH above)
  ```

- [ ] **Step 7: Verify all six registration points**

  Read `CLAUDE.md`. Confirm each of these is present and correct:
  - "Twelve operations" header
  - EXPAND operation block (between REFRESH and MERGE)
  - EXPAND row in skill-dispatch table
  - "expand" in hot-cache trigger sentence
  - "expand" in unattended CANNOT list
  - `/expand <page>` in slash-commands list

- [ ] **Step 8: Commit**

  ```
  git add CLAUDE.md
  git commit -m "docs(claude): register EXPAND operation (12th op, slash command, dispatch table, hot/unattended)"
  ```

---

## Task 3 — Update `/ingest` with map-then-read protocol

**Files:** Modify `commands/ingest.md`

**Context:** The current protocol reads a fixed page window (pp. 1–5 + last 2 for PDFs;
full body for web articles; full text for local-md). This is replaced by a three-step
map→propose→target-read protocol for all source types. The `≤3 new pages` guard is
replaced by the concept-list confirmation (the map makes the full list visible up front).

- [ ] **Step 1: Replace the Web articles protocol**

  Find:
  ```
  ### Web articles

  Source: `raw/web/<slug>/index.md` (no `fetch_method` field, or `fetch_method: html`).

  1. Read `index.md` — get `source_url`, `title`, `tags`, `note`.
  2. Read the article body.
  3. Write `wiki/sources/<slug>.md` with a summary in your own words.
  4. Propagate `tags` into the source frontmatter.
     If `note` is present, address that topic explicitly in the summary — not just
     acknowledge it.
  ```

  Replace with:
  ```
  ### Web articles

  Source: `raw/web/<slug>/index.md` (no `fetch_method` field, or `fetch_method: html`).

  1. Read `index.md` — get `source_url`, `title`, `tags`, `note`.
  2. **Map (cheap skim):** Read the article body and extract all section headings
     (H2–H4) plus the opening and closing paragraphs.
  3. **Propose concept list:** Present the proposed `wiki/pages/` entries to the
     user: "These N concepts → pages? [list]." Wait for the user to approve, add,
     or remove concepts before proceeding.
  4. **Read backing sections:** For each approved concept, read the specific
     section(s) of the article that support it.
  5. Write `wiki/sources/<slug>.md` and the concept pages following the page &
     source structure schema (see "Page & source structure" in CLAUDE.md).
  6. Propagate `tags` into the source frontmatter.
     If `note` is present, address that topic explicitly in the `## Summary` —
     not just acknowledge it.
  ```

- [ ] **Step 2: Replace the PDFs protocol**

  Find:
  ```
  ### PDFs

  Source: `raw/papers/<slug>/index.md` with `fetch_method: pdf`, **or**
  `raw/local/<slug>/index.md` with `fetch_method: local-pdf`.

  1. Read `index.md` — get `title`, `tags`, `note`.
     - For `fetch_method: pdf`: also read `source_url`.
     - For `fetch_method: local-pdf`: no `source_url` field; omit it everywhere.
  2. Read `paper.pdf` using the Read tool — pages 1–5. If the paper has more than
     10 pages, also read the last 2 pages.
  3. Infer the title from the first visible heading; fall back to the `title` in
     `index.md` frontmatter.
  4. Write `wiki/sources/<slug>.md` with the same schema as web sources.
     - For `fetch_method: pdf`: include `source_path: raw/papers/<slug>/` and
       `fetch_method: pdf` in the wiki source frontmatter.
     - For `fetch_method: local-pdf`: include `source_path: raw/local/<slug>/` and
       `fetch_method: local-pdf` in the wiki source frontmatter.
       Do **not** include a `source_url` field.
  5. Propagate `tags` and `note` as with other source types.
  ```

  Replace with:
  ```
  ### PDFs

  Source: `raw/papers/<slug>/index.md` with `fetch_method: pdf`, **or**
  `raw/local/<slug>/index.md` with `fetch_method: local-pdf`.

  1. Read `index.md` — get `title`, `tags`, `note`.
     - For `fetch_method: pdf`: also read `source_url`.
     - For `fetch_method: local-pdf`: no `source_url` field; omit it everywhere.
  2. **Map (cheap skim):** Read `paper.pdf` scanning all pages for section and
     subsection headings (H-level titles throughout the entire document — not limited
     to pages 1–5). Also read the abstract (typically page 1) and the conclusions
     section (typically the last 1–2 pages). This reveals the paper's full concept
     architecture without reading all body text.
  3. Infer the title from the first visible heading; fall back to the `title` in
     `index.md` frontmatter.
  4. **Propose concept list:** Present the proposed `wiki/pages/` entries to the
     user: "These N concepts → pages? [list]." Wait for the user to approve, add,
     or remove concepts before proceeding.
  5. **Read backing sections:** For each approved concept, read the specific pages
     or sections from `paper.pdf` that support it.
  6. Write `wiki/sources/<slug>.md` and the concept pages following the page &
     source structure schema.
     - For `fetch_method: pdf`: include `source_path: raw/papers/<slug>/` and
       `fetch_method: pdf` in the wiki source frontmatter.
     - For `fetch_method: local-pdf`: include `source_path: raw/local/<slug>/` and
       `fetch_method: local-pdf` in the wiki source frontmatter.
       Do **not** include a `source_url` field.
  7. Propagate `tags` and `note` as with other source types.
  ```

- [ ] **Step 3: Replace the Local Markdown files protocol**

  Find:
  ```
  ### Local Markdown files

  Source: `raw/local/<slug>/index.md` with `fetch_method: local-md`.

  1. Read `index.md` — get `title`, `source_url` (if present), `tags`, `note`.
  2. Read `content.md` in full (plain text; no page limit).
  3. Infer real title from content if better than `index.md` title
     (first H1 heading takes precedence over the filename-derived title).
  4. Write `wiki/sources/<slug>.md`:
     - Include `source_url` only if present in `index.md`.
     - `source_path: raw/local/<slug>/`
     - `fetch_method: local-md`
  5. Propagate `tags` and `note` as with other source types.
  ```

  Replace with:
  ```
  ### Local Markdown files

  Source: `raw/local/<slug>/index.md` with `fetch_method: local-md`.

  1. Read `index.md` — get `title`, `source_url` (if present), `tags`, `note`.
  2. Read `content.md` in full (plain text; no page limit).
  3. Infer real title from content if better than `index.md` title
     (first H1 heading takes precedence over the filename-derived title).
  4. **Map:** Extract all section headings (H2–H4) from `content.md` (already
     in context from step 2 — no additional reads needed).
  5. **Propose concept list:** Present the proposed `wiki/pages/` entries to the
     user: "These N concepts → pages? [list]." Wait for the user to approve, add,
     or remove concepts before proceeding.
  6. **Read backing sections:** For each approved concept, identify the specific
     sections in `content.md` that support it (file is already in context —
     no additional reads).
  7. Write `wiki/sources/<slug>.md` and the concept pages following the page &
     source structure schema:
     - Include `source_url` only if present in `index.md`.
     - `source_path: raw/local/<slug>/`
     - `fetch_method: local-md`
  8. Propagate `tags` and `note` as with other source types.
  ```

- [ ] **Step 4: Replace the Guards section**

  Find:
  ```
  ## Guards

  - **≤3 new pages before confirm.** If ingesting a source would require creating more
    than 3 new `wiki/pages/` entries for emerging concepts, stop and list the proposed
    pages. Ask: "Create all three?" before writing any.
  - **≤15 files per operation (invariant #6).** If a single ingest would touch more
    than 15 files, split across sessions. Report the count and ask which sources to
    prioritise.
  ```

  Replace with:
  ```
  ## Guards

  - **Concept-list confirmation.** The map-then-read protocol (steps 2–4 above) presents
    the full proposed concept list to the user before any writes. The user's approval of
    that list is the gate — there is no hard cap on the number of concepts created per
    ingest, provided the user explicitly approves the list.
  - **≤15 files per operation (invariant #6).** If a single ingest would touch more
    than 15 files, split across sessions. Report the count and ask which sources to
    prioritise.
  ```

- [ ] **Step 5: Verify the edit**

  Read `commands/ingest.md`. Confirm:
  - Web articles: 6 steps (Map, Propose, Read backing sections, Write, Propagate).
  - PDFs: 7 steps (map scans all pages for headings; no "pages 1–5" cap).
  - Local Markdown: 8 steps (map is free since file already in context).
  - Guards: "concept-list confirmation" replaces "≤3 new pages".
  - "≤15 files" guard is preserved.

- [ ] **Step 6: Commit**

  ```
  git add commands/ingest.md
  git commit -m "feat(ingest): map-then-read protocol — full heading scan + concept-list confirmation"
  ```

---

## Task 4 — Create `commands/expand.md`

**Files:** Create `commands/expand.md`

**Context:** A new interactive command following the `/refresh` anatomy exactly:
`description:` frontmatter → H1 → intro → `## Arguments` → `## Protocol` (numbered
steps) → `## Guards` → `## Unattended mode` → `## What /expand does NOT do` →
`## Report format`.

The full file content is stored at `features/prompts/expand-command-template.md`
to avoid nested code-fence rendering issues in this plan document.

- [ ] **Step 1: Read the template**

  Read `features/prompts/expand-command-template.md` in full. This is the exact
  content that must be written to `commands/expand.md` — do not modify it.

- [ ] **Step 2: Copy template to the command file**

  Write `commands/expand.md` with exactly the content from the template file.
  The file must begin with the YAML frontmatter (`---`) and end with the report
  format code block. Do not add or remove any lines.

- [ ] **Step 3: Verify the file**

  Read `commands/expand.md`. Confirm:
  - Single `description:` frontmatter key with a multi-line folded value.
  - H1 is `# /expand — Deepen a wiki page`.
  - Protocol has 6 numbered `###` steps.
  - Step 5 explicitly handles both the "absent" and "already exists" cases.
  - Step 5 shows the `expanded: YYYY-MM-DD` frontmatter key in a yaml code block.
  - Guards, Unattended mode, What /expand does NOT do, Report format sections all present.
  - Report format ends with `→ Run /review to find other pages worth expanding`.

- [ ] **Step 4: Commit**

  ```
  git add commands/expand.md features/prompts/expand-command-template.md
  git commit -m "feat(commands): add /expand — deepen a wiki page from its full source"
  ```

---

## Task 5 — Wire `/review` Check C to `/expand`

**Files:** Modify `commands/review.md`

**Context:** Step 9 of the review protocol lists suggested next actions. The "Summary
quality" bullet currently says "consider expanding the summary or adding cross-links"
— this is now a dead end (no command to run). Replace it to point to `/expand`.

- [ ] **Step 1: Update step 9's summary-quality suggestion**

  Find:
  ```
     - Summary quality → "consider expanding the summary or adding cross-links"
  ```

  Replace with:
  ```
     - Summary quality (thin) → "consider `/expand <page>` to deepen from the full source, or add cross-links"
  ```

- [ ] **Step 2: Verify**

  Read `commands/review.md`. Confirm:
  - The Contradictions and Faithfulness bullets are unchanged.
  - The Summary quality bullet now mentions `/expand <page>`.
  - No other lines were modified.

- [ ] **Step 3: Commit**

  ```
  git add commands/review.md
  git commit -m "docs(review): wire Check C thin-page suggestion to /expand"
  ```

---

## Task 6 — Doc sync: `README.md` and `GETTING-STARTED.md`

**Files:** Modify `README.md`, modify `GETTING-STARTED.md`

**Context:** Both files enumerate slash commands. `README.md` shows the command file
tree. `GETTING-STARTED.md` has an operations table (numbered 1–11) and a bullet list
of commands. Both need `/expand` added to match the new 12-operation system.

- [ ] **Step 1: Update README.md command file tree**

  Find:
  ```
  │   ├── refresh.md            /refresh
  │   ├── retry.md              /retry
  ```

  Replace with:
  ```
  │   ├── refresh.md            /refresh
  │   ├── expand.md             /expand
  │   ├── retry.md              /retry
  ```

- [ ] **Step 2: Update GETTING-STARTED.md operations table**

  Find:
  ```
  | 11 | **MERGE** | `/merge <page-A> <page-B>` or *"merge these pages"* / `/split <page> <a> <b>` or *"split this page"* | Resolve near-duplicate pages: merge two into one canonical page with full backlink rewriting, or split an overgrown page into two. Interactive only; never available unattended |
  ```

  Replace with:
  ```
  | 11 | **MERGE** | `/merge <page-A> <page-B>` or *"merge these pages"* / `/split <page> <a> <b>` or *"split this page"* | Resolve near-duplicate pages: merge two into one canonical page with full backlink rewriting, or split an overgrown page into two. Interactive only; never available unattended |
  | 12 | **EXPAND** | `/expand <page>` or *"expand this page"* | Read cited source(s) in full and append a `## Deep dive` section to the page for in-depth treatment. Overview sections remain unchanged. Interactive only; never available unattended |
  ```

- [ ] **Step 3: Update GETTING-STARTED.md bullet command list**

  Find:
  ```
  - **`/refresh <source>`** — re-fetch a source whose content has
    changed, re-ingest it, and flag pages that may need review.
  ```

  Replace with:
  ```
  - **`/refresh <source>`** — re-fetch a source whose content has
    changed, re-ingest it, and flag pages that may need review.
  - **`/expand <page>`** — deepen an existing page by reading its cited
    source(s) in full and appending a `## Deep dive` section. Leaves
    the overview sections intact. Interactive only. Use `/review` to
    discover which pages are thin enough to benefit.
  ```

- [ ] **Step 4: Verify both files**

  Read `README.md` — confirm `expand.md` appears in the tree between `refresh.md`
  and `retry.md`.

  Read `GETTING-STARTED.md` — confirm:
  - Row 12 (EXPAND) appears in the operations table.
  - The `/expand <page>` bullet appears after `/refresh <source>`.

- [ ] **Step 5: Commit**

  ```
  git add README.md GETTING-STARTED.md
  git commit -m "docs: add /expand to README file tree and GETTING-STARTED operations table"
  ```

---

## Task 7 — End-to-end verification

**Context:** All changes are prompt/protocol prose. Verification is behavioral, not
unit-tested. Use a scratch vault (or an existing test vault if available).

- [ ] **Step 1: Lint clean on a scratch vault**

  Bootstrap a scratch vault (run from `D:\my-2nd-brain`):
  ```
  python init_vault.py C:\temp\scratch-vault
  ```

  Create a minimal test page with the new frontmatter key and section:
  ```
  C:\temp\scratch-vault\wiki\pages\test-page.md
  ```
  Content:
  ```
  ---
  type: page
  created: 2026-05-30
  updated: 2026-05-30
  expanded: 2026-05-30
  tags: []
  ---

  Test concept.

  ## Overview
  A test page used to verify that the expanded frontmatter key and Deep dive section
  do not trigger any new lint findings.

  ## Key dimensions

  ### Testing
  Used for lint verification only. [[wiki/sources/test-source]]

  ## Connections
  - (none)

  ## Sources
  - [[wiki/sources/test-source]] — synthetic source for testing

  ## Deep dive
  Full treatment would appear here after running /expand.
  ```

  Run the linter:
  ```
  python skills/vault-linter/scripts/lint.py C:\temp\scratch-vault
  ```

  Expected: exit 0 or exit 1 with only expected findings (dead link to
  `test-source` is fine — confirms the linter runs and the `expanded:` key and
  `## Deep dive` section do not cause any new finding categories).

- [ ] **Step 2: Coverage check — map-then-read**

  In a scratch vault, add a PDF index stub that references a multi-section document.
  Start an ingest session. Confirm the agent proposes a concept list based on section
  headings (not just abstract + conclusion).

- [ ] **Step 3: Depth check — /expand**

  Run `/expand <page>` on a page in a scratch vault. Verify:
  - `## Deep dive` section appears in the page file.
  - `## Overview` and `## Key dimensions` are unchanged.
  - `updated` and `expanded` frontmatter keys are bumped.
  - `wiki/index.md` entry is updated (shows "expanded" marker).
  - `wiki/log.md` has the `expand | <slug>` entry.

- [ ] **Step 4: Idempotency check**

  Re-run `/expand` on the same page. Confirm `## Deep dive` is refreshed in place
  (not duplicated). Confirm `expanded:` date is updated to today.

- [ ] **Step 5: Review driver check**

  Run `/review` on a vault with a thin page (< 3 substantive sentences). Confirm
  Check C finding now reads "consider `/expand <page>` to deepen from the full
  source" (not the old "consider expanding the summary").

- [ ] **Step 6: Unattended guard check**

  Attempt `/expand` with `VAULT_UNATTENDED=1` set. Confirm the command refuses with
  a clear message.

- [ ] **Step 7: Final commit — push branch**

  Confirm all tasks are committed on `feat-deepdive`:
  ```
  git log --oneline -7
  ```

  Expected commits (one per task):
  ```
  docs: add /expand to README file tree and GETTING-STARTED operations table
  docs(review): wire Check C thin-page suggestion to /expand
  feat(commands): add /expand — deepen a wiki page from its full source
  feat(ingest): map-then-read protocol — full heading scan + concept-list confirmation
  docs(claude): register EXPAND operation (12th op, slash command, dispatch table, hot/unattended)
  docs(claude): add adaptive page/source structure schema
  ```
