---
description: Deepen an existing wiki page by reading its cited source(s) in full
  and appending a comprehensive ## Deep dive section. Leaves the Overview and Key
  dimensions sections intact — they remain the link target and scannable entry point.
  Interactive — not available in unattended mode.
---

# /expand — Deepen a wiki page

Add in-depth treatment to an existing page by reading its cited source(s) in full
(no page-window limit) and writing a `## Deep dive` section below the standard
overview sections. The `## Overview` and `## Key dimensions` sections remain
unchanged — they continue to serve as the link target.

Re-running `/expand` refreshes `## Deep dive` in place; it does not duplicate the
section.

## Arguments

`/expand <page>` where `<page>` can be:

- A slug: `/expand rag-retrieval`
- A wiki path: `/expand wiki/pages/rag-retrieval.md`

## Protocol

> **Windows:** replace `python3` with `python` in all commands below.

### 1. Resolve page

Read `wiki/pages/<slug>.md`. Confirm with the user: show the page title and the
sources listed in its `## Sources` section.

### 2. Assess sources

For each source cited in `## Sources`:

1. Read `wiki/sources/<slug>.md` to find `source_path` and `fetch_method`.
2. Count files this operation will touch: the page file + each source file read.
   If the total exceeds **15 files** — stop and report the fanout. Let the user
   pick which sources to expand from in this pass.

### 3. Read sources in full

Read each cited source completely — no page-window limits:

- **Web articles** (`fetch_method` absent or `html`): read the full article body
  at `raw/web/<slug>/index.md`.
- **PDFs** (`fetch_method: pdf` or `local-pdf`): read `paper.pdf` with no page
  limit — read all pages.
- **Local Markdown** (`fetch_method: local-md`): read `content.md` in full (this
  is already the default for local-md — no change from normal ingest behavior).

### 4. Draft the Deep dive section

Write a draft `## Deep dive` section covering: methodology or approach, key
evidence or examples, nuance and trade-offs, limitations or open questions.

Show the draft to the user and wait for approval before writing. Do not modify
`## Overview`, `## Key dimensions`, `## Connections`, or `## Sources` — those
sections must remain exactly as they are.

### 5. Write the Deep dive section

If `## Deep dive` does not exist in the page, append it below `## Sources`.
If `## Deep dive` already exists (from a previous `/expand` run), replace its
content in place — do not create a duplicate section.

Add or update the `expanded` frontmatter key and bump `updated` to today:

```yaml
expanded: YYYY-MM-DD
updated: YYYY-MM-DD
```

### 6. Bookkeeping

- `wiki/index.md`: update the page's entry — append ` (expanded)` after the page
  title to mark it as having a Deep dive section.
- `wiki/log.md`: append one line:
  `## [YYYY-MM-DD] expand | <slug>`

---

## Guards

**Prose-deletion guard:** Never modify or delete `## Overview`, `## Key dimensions`,
`## Connections`, or `## Sources` content. Show the draft (step 4) before writing
and check that it contains only the `## Deep dive` section.

**Fanout guard (>15 files):** If reading all cited sources would touch more than 15
files, stop immediately. List the sources and their file counts. Let the user pick
which to include in this pass.

**Shareable view guard:** `/expand` writes only to `wiki/pages/`. It does not touch
views. No shareable-view interaction.

## Unattended mode

`/expand` is **not available unattended**. The operation involves a full-source read
(potentially high token cost) and a prose rewrite that requires user review of the
draft. If invoked unattended, refuse with a clear message and suggest running the
command interactively.

## What /expand does NOT do

- Does not re-ingest the source — use `/refresh <source>` if the source content has
  changed.
- Does not create new `wiki/pages/` entries — it deepens an existing page only.
- Does not modify `wiki/sources/` files.
- Does not run automatically — use `/review` to discover which pages are worth
  expanding (Check C flags thin pages).

## Report format

End of EXPAND operation, tell the user:

```
Expanded: wiki/pages/<slug>.md
  ✓ Read <N> source(s) in full
  ✓ Added ## Deep dive section
  ✓ Updated frontmatter: expanded: YYYY-MM-DD
  ✓ Updated wiki/index.md and wiki/log.md
  → Run /review to find other pages worth expanding
```
