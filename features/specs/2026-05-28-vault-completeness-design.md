# Vault Completeness Design

**Date:** 2026-05-28
**Scope:** Documentation and protocol completeness — no Python changes, no tests

---

## Context

The vault has two completed build cycles behind it. The foundation (config layer,
shared state, PDF folders, tags/note propagation, nine operations, skill manifests)
and the hardening pass (fetch pipeline fixes, three new linter checks, session
lifecycle, Obsidian skeleton) are both stable.

This cycle closes the gap between what the vault does and what its documentation
and slash commands say it does. Every item here makes an existing feature
fully reachable or correctly described — no new architectural concepts.

---

## File Summary

| File | Type | Change |
|------|------|--------|
| `commands/fetch.md` | New | Slash command entry point for the FETCH operation |
| `commands/hot.md` | New | Slash command for flushing session state to `wiki/hot.md` |
| `commands/playwright-fetch.md` | New | Authoritative Playwright fallback protocol |
| `CLAUDE.md` | Edit | Three targeted replacements: session-start reflect check, session-end hot.md instruction, FORGET cascade step 5 |
| `commands/ingest.md` | Edit | Add pre-ingest deduplication check before web/PDF branches |
| `commands/refresh.md` | Edit | Replace steps 1–3 with source-type-branching protocol |
| `skills/vault-linter/SKILL.md` | Edit | Update check count, table, severity notes to reflect 13 checks |
| `skills/inbox-fetcher/SKILL.md` | Edit | Replace Playwright section with 3-line pointer to command |
| `init-vault.sh` | Edit | Extend command install loop with `fetch hot playwright-fetch` |

9 files. All markdown except one shell script line.

---

## Section 1 — New Slash Commands

### `commands/fetch.md`

Thin dispatch entry point. The script and skill file own the implementation
detail; this file is the named agent entry point for the FETCH operation,
consistent with every other operation having a slash command.

```markdown
---
description: Process the URL queue in inbox.md. Downloads web articles and PDFs
  into raw/, marks successful fetches as done, and leaves failed URLs with ⚠ markers
  for Playwright fallback. Run before /ingest.
---

# /fetch — Process the inbox

## When to use

When inbox.md has unchecked URLs (`- [ ]`) and you want to download them.
Triggered by: "process the inbox", "fetch the URLs", "download these articles".

Always run /fetch before /ingest — ingest needs raw/ files to summarise.

## How to run

```bash
python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
```

Or dry-run to preview without writing:
```bash
python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --dry-run
```

## After running

1. Report the summary (✓ HTML, ✓ PDF, ⚠ failed counts).
2. For any `⚠ ... — try playwright` URLs, offer to run `/playwright-fetch`
   to retrieve them interactively via the browser.
3. When there are no remaining ⚠ markers (or the user skips Playwright),
   offer to run `/ingest` on the newly downloaded files.
```

---

### `commands/hot.md`

Explicit command for flushing session state to `wiki/hot.md`. Makes the
session-end update observable rather than a side effect that may be silently
skipped. CLAUDE.md's session-end instruction will reference this command.

```markdown
---
description: Write or update wiki/hot.md with a brief record of what was covered
  this session, what's still open, and what to pick up next. Run at session end
  after any wiki/ writes. Replaces the previous entry — never appends.
---

# /hot — Update the session hot cache

## When to use

At the end of any session in which wiki/ was written to (ingest, promote,
view, forget, reflect, refresh). Also useful mid-session to checkpoint state.

The user can call this explicitly. The agent should call it automatically
before giving its final response in a writing session.

## What to write

5–10 lines covering three things:

1. **What we did** — sources ingested, pages touched, views built,
   decisions made (slug names, tag choices, structural calls).
2. **What's open** — any ⚠ linter findings not resolved, deferred
   decisions, unfinished trains of thought.
3. **What to pick up next** — the single most useful thing to do
   next session, stated concretely.

## Format

```markdown
## [YYYY-MM-DD]

[5-10 lines of prose or bullets — no headers inside]
```

Replace the entire file. Do not append. The hot cache is a snapshot,
not a log (`wiki/log.md` is the append-only record).
```

---

### `commands/playwright-fetch.md`

Extracts the per-URL interactive protocol that was previously embedded
in `skills/inbox-fetcher/SKILL.md`. Moving it to a command file makes
it a named, invocable entry point rather than a buried implementation note.

```markdown
---
description: Retrieve walled, paywalled, or JS-rendered URLs that the inbox
  fetcher could not download. Uses the Playwright MCP browser interactively,
  one URL at a time, with user confirmation per URL. Run after /fetch leaves
  ⚠ try playwright markers in inbox.md.
---

# /playwright-fetch — Retrieve URLs via browser

## When to use

After `/fetch`, when inbox.md contains lines marked:
```
- [ ] https://example.com/article ⚠ walled domain — try playwright
- [ ] https://paywall.com/piece ⚠ extraction empty — try playwright
```

## One URL at a time

Never batch-process walled URLs unattended. Each URL requires:
1. Confirm with the user before navigating.
2. Navigate with `browser_navigate`.
3. If auth is required: stop and report — do not attempt to bypass.
4. Extract content with `browser_snapshot` (accessibility tree) or
   `browser_evaluate` (DOM extraction). For X/Twitter threads: collect
   the full thread, not just the root post.

## Writing the output

For each successfully retrieved URL, write `raw/web/<slug>/index.md`:

```yaml
---
source_url: <url>
title: <inferred or first line>
author: <handle or author name>
published: <YYYY-MM-DD if visible>
fetched: <today>
fetched_via: playwright
---
```

Slug: prefer article title; for X/Twitter use `<handle>-<tweet-id>`.

Save screenshots to `raw/web/<slug>/assets/` only if the user asks.

## Inbox update

For each success, update inbox.md: move the line to `## Processed`
with `- [x] <url> → \`raw/web/<slug>/\` (<today>)`. Remove the ⚠ marker.

For each failure, keep the line unchecked. Append the failure reason
after ⚠ and ask the user how to proceed.

## After

When all ⚠ URLs have been attempted, report outcomes and offer `/ingest`
on the newly written files.

## Out of scope

- Bypassing login walls or solving CAPTCHAs.
- Batch processing (every URL needs a confirmation).
- Any URL not already marked ⚠ by `/fetch`.
```

---

### `init-vault.sh` — command loop extension

The install loop that copies command files into `.claude/commands/` needs
the three new names:

```bash
# Before
for cmd in save view reflect forget lint promote refresh ingest; do

# After
for cmd in save view reflect forget lint promote refresh ingest fetch hot playwright-fetch; do
```

---

## Section 2 — CLAUDE.md Protocol Fixes

Three targeted replacements. No new sections; no structural changes.

### Session start — reflect reminder (rule #3)

The current rule says "hasn't been updated" without specifying where to look.
The `updated` field in `wiki/compass.md` frontmatter is the canonical source.

**Current:**
> If `wiki/compass.md` hasn't been updated in more days than
> `lint.reflect_reminder_days` (from `vault.config.yml`), suggest running `/reflect`.

**Replace with:**
> Read the `updated` field from `wiki/compass.md` frontmatter. If the file is
> absent or its `updated` date is more than `lint.reflect_reminder_days` days
> ago, suggest running `/reflect`.

---

### Session end — hot.md instruction

The `## Hot cache` section body currently uses "meaningful content" (undefined)
and "session end" (no hook). Both are replaced with an actionable rule that
references the new `/hot` command.

**Current body of `## Hot cache`:**
> At session end, if we touched meaningful content, update `wiki/hot.md`
> with 5-10 lines on what we covered, what's open, what's next.
> Don't add — replace.

**Replace with:**
> After any session in which `wiki/` was written to, run `/hot` before the
> final response. "Written to" means any ingest, promote, view, reflect,
> forget, or refresh that produced file changes — not queries.
>
> `/hot` replaces the entire file. `wiki/log.md` is the append-only record;
> `wiki/hot.md` is the current snapshot.

---

### FORGET cascade — raw folder deletion (step 5)

The current step 5 says "delete the `raw/` file." For both web articles
(`raw/web/<slug>/`) and PDFs (`raw/papers/<slug>/`), the "file" is a folder
containing downloaded assets. Deleting only the index leaves assets/ behind.

**Current step 5:**
> Delete `wiki/sources/<slug>.md` and the `raw/` file. This is the
> one case where writing to `raw/` (as deletion) is allowed —
> invariant #1 covers creation, not user-directed removal.

**Replace with:**
> Delete `wiki/sources/<slug>.md`. Delete the entire raw folder:
> - Web sources: `raw/web/<slug>/` (includes `index.md` and `assets/`).
> - PDF sources: `raw/papers/<slug>/` (includes `paper.pdf` and `index.md`).
>
> This is the one case where writing to `raw/` (as deletion) is allowed —
> invariant #1 covers creation, not user-directed removal.

---

## Section 3 — Updates to Existing Command Files

### `commands/ingest.md` — pre-ingest deduplication check

Add a `## Pre-ingest check` subsection before the existing `## Protocol`
web/PDF branches. It runs before the confirm threshold, not instead of it.

```markdown
## Pre-ingest check

Before writing any new `wiki/pages/` entry, scan the existing pages directory
for a file whose name closely matches the proposed concept name (case-insensitive,
ignore articles and punctuation). If a close match exists:

- **Update the existing page** rather than creating a new one.
- Cite the new source alongside any existing citations already on that page.
- Do not create a second page for the same concept under a different slug.

If two sources being ingested in the same session both reference the same
emerging concept, create the page once during the first source and update
it during the second. Track which pages were created or updated this session
to avoid proposing duplicates mid-session.
```

---

### `commands/refresh.md` — PDF branch in protocol

Steps 1–3 of the current protocol treat all sources identically. PDFs
served from permanent URLs (papers, archived documents) rarely change;
the re-fetch step is unnecessary friction for them. The resolution is
a branch at step 2 based on `fetch_method` in the source frontmatter.

**Replace steps 1–3 with:**

```markdown
1. **Resolve slug.** Find `wiki/sources/<slug>.md` and read `source_url`
   and `fetch_method` from its frontmatter. Confirm with the user:
   show title, source_url, and fetch_method.

2. **Branch by source type.**

   **Web article** (`fetch_method` absent or `html`):
   Add the URL back to `inbox.md` as an unchecked entry under "To process".
   Instruct the user to run the fetcher to overwrite the raw folder:
   ```bash
   python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
   ```
   Wait for the fetcher to complete before proceeding to step 3.

   **PDF source** (`fetch_method: pdf`):
   Ask the user: "This is a PDF source — PDFs rarely change. Re-fetch
   the file from the original URL, or re-summarise from the existing
   `raw/papers/<slug>/paper.pdf`?"
   - **Re-fetch:** add URL to `inbox.md` and proceed as the web article
     branch above.
   - **Re-summarise:** skip to step 3 directly, using the existing
     `paper.pdf`.

3. **Re-ingest.** Rewrite `wiki/sources/<slug>.md` with an updated
   summary. Bump `updated` to today.
```

Steps 4 and 5 (flag affected pages, update log) are unchanged.

---

## Section 4 — Skill Documentation Fixes

### `skills/vault-linter/SKILL.md`

Three stale spots updated to reflect the 13-check reality:

**Frontmatter description** — extend the check list to include:
`view based_on dead links, PDF index integrity, conversation schema, source index sync`

**Section heading and table** — "Nine deterministic checks" → "Thirteen
deterministic checks". Add four rows:

| # | Check | What it catches |
|---|---|---|
| 10 | **Based-on dead links** | `based_on` entries in view frontmatter pointing to non-existent pages |
| 11 | **PDF index integrity** | `raw/papers/` subdir missing `index.md`, or legacy flat `.pdf` in `raw/papers/` |
| 12 | **Conversation schema** | `conversations/` files missing `type: conversation` frontmatter |
| 13 | **Source index sync** | `wiki/sources/` entry not mentioned in `wiki/index.md` |

**Severity section** — extend to place new checks at their correct levels:

```
- **Blocking** — dead links, missing required metadata, based-on dead links.
- **Important** — orphans.
- **Advisory** — duplicates, stale, naming, view staleness, gaps,
  missing cross-references, PDF index integrity, conversation schema,
  source index sync.
```

---

### `skills/inbox-fetcher/SKILL.md`

The `## Playwright fallback` section (30+ lines) is replaced with a
3-line pointer. The protocol itself now lives in `commands/playwright-fetch.md`.

**Replace entire `## Playwright fallback` section with:**

```markdown
## Playwright fallback

Any URL marked `⚠ ... — try playwright` in inbox.md is a hand-off from
the script to the agent. Use the `/playwright-fetch` command — it contains
the full per-URL protocol.
```

---

## Invariants — unchanged

All six vault invariants remain intact. Section 2's FORGET update
clarifies the scope of deletion in invariant #1's exception clause
without changing its meaning.
