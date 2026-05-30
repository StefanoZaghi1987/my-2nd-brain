# Ingest Depth & Coverage — Design Spec
**Date:** 2026-05-30
**Branch:** feat-deepdive
**Status:** approved

---

## 0. Repo orientation

`D:\my-2nd-brain` is the **template/engine repo** — it generates second-brain
vaults via `init_vault.py`. No `wiki/`, `raw/`, or `inbox.md` exists on disk
here; those are created in the target directory at bootstrap. Key layout:

```
CLAUDE.md               LLM operating contract — installed into every vault
commands/               Slash command protocols (Markdown, one file per command)
skills/
  inbox-fetcher/        URL queue + drop-zone adoption
  vault-linter/         14 deterministic checks (lint.py)
  view-builder/         7 view-kind templates + LLM
  shared/               find_backlinks.py, linkutil.py, vault_state.py …
features/
  specs/                Design specs (this file)
  plans/                Implementation plans
  backlog/tasks/        Backlog.md task files
```

---

## 1. Problem

Two independent failures make ingested wiki pages feel thin:

1. **Shallow treatment (depth).** The generation step has no contract. `/ingest`
   says only "write a summary in your own words" (`commands/ingest.md:73`) with
   no target structure, section schema, or required dimensions. Unspecified
   output → minimized output. The `view-builder` ships 7 view templates that
   shape its output; pages and sources have no equivalent.

2. **Missing concepts (coverage).** PDFs are read with a fixed page window
   (pages 1–5, plus last 2 if >10pp, `commands/ingest.md:86-87`). A 30-page
   paper is summarized from a 7-page window; every concept buried in methods,
   experiments, or appendices never enters the vault. The `≤3 new pages` guard
   (`ingest.md:114`) further caps concept extraction without first showing what
   concepts are available.

The only quality backstop — "thin = <~3 sentences" (`commands/review.md:78`) —
is a retroactive detector in `/review`, not a generation target.

**Out of scope:** cross-source synthesis (that's a future `/synthesize` or
enhanced `/merge` concern).

---

## 2. Design decisions (locked with user)

| Decision | Choice |
|----------|--------|
| Delivery model | Blended two-pass: better default (coverage) + on-demand depth (`/expand`) |
| Default read strategy | Map-then-read: cheap full skim → concept proposal → targeted section reads |
| `/expand` output location | Append `## Deep dive` section to the same page file; no `.deep.md` suffix |

---

## 3. Solution

### 3.1 Page & source structure schema

A new **"Page & source structure"** section is added to `CLAUDE.md` (after the
Frontmatter section, before "Eleven operations"). This is the missing template —
it turns an open-ended "summarize" into a coverage checklist.

**Schema is adaptive:** "cover these sections where the source supports them."
No section should be padded with "none discussed."

**`wiki/sources/<slug>.md` body:**
```
<One-line capsule: author, venue, type, date.>

## Summary
2–5 paragraphs, own words. If a `note` directive was supplied, address it
explicitly here (not just acknowledge it).

## Key points
Bulleted substantive claims, each traceable to the raw source.

## Connections
[[wiki/pages/<concept>]] links this source touches, with a one-phrase note.
```

**`wiki/pages/<slug>.md` body:**
```
<One-line definition.>

## Overview
3–6 sentences: what it is, why it matters, key variants.
This section is what incoming links resolve to — keep it scannable.

## Key dimensions
Adaptive H3 subsections — one per facet the available sources support.
Each: 1–3 sentences + inline citation to [[wiki/sources/slug]].

## Connections
Related pages via [[wiki/pages/...]] with relationship phrase.

## Sources
[[wiki/sources/slug]] entries with one-phrase role.

## Deep dive
Added only by /expand. Absent on standard ingested pages.
Full treatment: methodology, evidence, nuance, limitations.
```

### 3.2 Map-then-read in `/ingest` (coverage fix)

Replace the fixed page-window reads in `commands/ingest.md` with a three-step
protocol applied to all source types:

**Step A — Map (cheap full skim):**
- Web articles: read all section headings (H2–H4) + opening + closing paragraphs.
- PDFs: read the full heading structure (scan all pages for H-level titles) +
  abstract (p.1) + conclusions section. No page cap on the heading scan.
- Local Markdown: already read in full — extract headings for the map.

**Step B — Propose concept list:**
Present the proposed `wiki/pages/` entries to the user: "These N concepts →
pages? [list]." Wait for approval/modification. This replaces the bare `≤3 new
pages` stop — the map makes the full list visible up front, and the user's
approval of that list is the confirmation gate.

**Step C — Read backing sections:**
For each approved concept, read only the specific sections from the source that
support it. This is targeted, not full-text.

**Step D — Write** sources + pages using the structure schema (§3.1).

The `≤15 files/op` invariant guard is preserved. The `≤3 new pages` hard stop
is replaced by the B-step concept-list confirmation (which handles any count).

### 3.3 New `/expand <page>` command (depth fix)

New file `commands/expand.md`. Follows the `/refresh` command anatomy exactly:
single `description:` frontmatter, H1, `## Arguments`, numbered `## Protocol`,
`## Guards`, `## Unattended mode`, `## Report format`.

**Arguments:** `/expand <page>` — slug or `wiki/pages/<slug>.md`.

**Protocol:**
1. Resolve the page; read it and the `## Sources` section to find cited sources.
2. Read each cited source **in full** (no page window for PDFs; local-md already
   full; web articles read complete body).
3. If full reads would push the operation past 15 files, report fanout and let
   the user pick scope.
4. Draft the `## Deep dive` section content and show it to the user.
5. Write/refresh the `## Deep dive` section below `## Sources`. Leave
   `## Overview` and `## Key dimensions` completely intact — they remain the
   link target and the scannable entry point.
6. Bump `updated`; add `expanded: YYYY-MM-DD` to frontmatter as a provenance
   marker (visible to `/review` Check C and future tooling).
7. Update `wiki/index.md` (mark page as expanded) and append
   `## [YYYY-MM-DD] expand | <slug>` to `wiki/log.md` (Invariant #6).

**Guards:** prose-deletion (never drop overview content without confirm); ≤15
file fanout; never touch `shareable: true` views.

**Unattended:** not available (deliberate rewrite + token-heavy full read).

**Idempotency:** re-running `/expand` on the same page refreshes `## Deep dive`
in place; it does not duplicate the section.

### 3.4 Wire EXPAND into system docs (`CLAUDE.md`)

Six changes to `CLAUDE.md`:
1. **Operation count header:** `## Eleven operations` → `## Twelve operations`.
2. EXPAND operation entry (after REFRESH, before MERGE section).
3. `/expand <page>` in the Slash commands list.
4. EXPAND row in the Skill dispatch table (LLM only, no script).
5. "expand" added to the `/hot` "written to" trigger list.
6. `/expand` added to the Unattended mode CANNOT list.

### 3.5 `/review` becomes the depth driver (`commands/review.md`)

One-line change in step 9's suggestions: the "Summary quality" bullet currently
says "consider expanding the summary or adding cross-links." Replace with:
"consider `/expand <page>` to deepen from the full source, or add cross-links."

This closes the detect→act loop: `/review` Check C finds thin pages → user
runs `/expand` on the ones worth it.

### 3.6 Doc sync (`README.md`, `GETTING-STARTED.md`)

Add `/expand` to any command listing tables/sections that enumerate slash
commands. Match the same phrasing used for `/refresh`.

---

## 4. Files to create / modify

| File | Change type |
|------|------------|
| `CLAUDE.md` | Modify — add schema section + EXPAND op + 4 registration points |
| `commands/ingest.md` | Modify — map-then-read protocol for all source types + guard reframe |
| `commands/expand.md` | **Create** — new command (follows `/refresh` anatomy) |
| `commands/review.md` | Modify — one-line suggestion in step 9 |
| `README.md` | Modify — add `/expand` to command listing |
| `GETTING-STARTED.md` | Modify — add `/expand` to command listing |

No changes to `lint.py` or any Python script.
No changes to `raw/` or vault content (this is a template repo).

---

## 5. Invariant compliance

| Invariant | Impact |
|-----------|--------|
| #1 Never write to `raw/` | Not affected — all changes are command/CLAUDE.md prose |
| #2 Every claim cites a source | Not affected |
| #3 Paraphrase, don't copy | Not affected |
| #4 User curates, you maintain | `/expand` is interactive-only; respects the guard |
| #5 ≤15 files per operation | `/expand` Guard §3.3 step 3 enforces this |
| #6 Update index + log | `/expand` Protocol step 7 enforces this |

---

## 6. Verification

Since all deliverables are prompt/protocol prose, verification is behavioral:

1. **Lint clean:** run `python skills/vault-linter/scripts/lint.py <scratch-vault>`
   on a test vault that includes a page with `expanded: YYYY-MM-DD` frontmatter
   and a `## Deep dive` section. Confirm no new lint findings (exit 0 or 1 with
   pre-existing issues only).

2. **Coverage — map-then-read:** ingest a long (>10pp) PDF in a scratch vault.
   Confirm the agent proposes a concept list that includes concepts from
   mid-document sections (not only intro/conclusion).

3. **Depth — `/expand`:** run `/expand <page>` on a standard page. Confirm:
   `## Deep dive` section appears; `## Overview` and `## Key dimensions` are
   unchanged; `updated` and `expanded` frontmatter keys are bumped;
   `wiki/index.md` and `wiki/log.md` are updated.

4. **Driver loop:** run `/review` on a vault with a thin page. Confirm Check C
   suggests `/expand <page>` (not just "expand the summary").

5. **Idempotency:** re-run `/expand` on the same page. Confirm `## Deep dive`
   is refreshed in place — not duplicated.

6. **Guards:** attempt `/expand` in unattended mode. Confirm refusal. Attempt
   on a page citing >15 sources. Confirm fanout report and stop.
