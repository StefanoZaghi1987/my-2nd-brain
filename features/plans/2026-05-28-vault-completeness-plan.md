# Vault Completeness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the gap between what the vault does and what its documentation and slash commands say it does — 9 files changed, all markdown or shell, no Python.

**Architecture:** All changes are independent. Three new command files establish missing slash command entry points. Three CLAUDE.md edits sharpen protocol language. Two existing command files gain protocol extensions. Two SKILL.md files are corrected. One shell script line is extended. No sequencing dependencies — any task can start first.

**Tech Stack:** Markdown, YAML frontmatter, bash. Edit tool for targeted replacements; Write tool for new files.

**Spec:** `features/specs/2026-05-28-vault-completeness-design.md`

**Working directory:** `D:\my-2nd-brain` — all paths relative to this directory.

**Comment rule:** Only descriptive/explanatory comments (the WHY of non-obvious decisions). Never reference tasks, issues, or feature names in comments.

---

## Task 1 — Create `commands/fetch.md`

**Files:**
- Create: `commands/fetch.md`

- [ ] **Step 1: Write the file**

Create `commands/fetch.md` with this exact content:

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

- [ ] **Step 2: Verify**

```bash
cat commands/fetch.md
```

Expected: file exists, frontmatter description ends with "Run before /ingest.", three numbered steps in "After running".

- [ ] **Step 3: Commit**

```bash
git add commands/fetch.md
git commit -m "add /fetch slash command for inbox processing"
```

---

## Task 2 — Create `commands/hot.md`

**Files:**
- Create: `commands/hot.md`

- [ ] **Step 1: Write the file**

Create `commands/hot.md` with this exact content:

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

- [ ] **Step 2: Verify**

```bash
cat commands/hot.md
```

Expected: file exists, three numbered "What to write" items, "Replace the entire file" note at end.

- [ ] **Step 3: Commit**

```bash
git add commands/hot.md
git commit -m "add /hot slash command for session state flushing"
```

---

## Task 3 — Create `commands/playwright-fetch.md`

**Files:**
- Create: `commands/playwright-fetch.md`

- [ ] **Step 1: Write the file**

Create `commands/playwright-fetch.md` with this exact content:

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

- [ ] **Step 2: Verify**

```bash
cat commands/playwright-fetch.md
```

Expected: file exists, "One URL at a time" section with 4 steps, "Out of scope" section with 3 bullets.

- [ ] **Step 3: Commit**

```bash
git add commands/playwright-fetch.md
git commit -m "add /playwright-fetch slash command for browser-based URL retrieval"
```

---

## Task 4 — Update `init-vault.sh` command install loop

**Files:**
- Modify: `init-vault.sh:334`

- [ ] **Step 1: Extend the command loop**

In `init-vault.sh` at line 334, replace:

```bash
for cmd in save view reflect forget lint promote refresh ingest; do
```

With:

```bash
for cmd in save view reflect forget lint promote refresh ingest fetch hot playwright-fetch; do
```

- [ ] **Step 2: Verify**

```bash
grep "for cmd in" init-vault.sh
```

Expected: `for cmd in save view reflect forget lint promote refresh ingest fetch hot playwright-fetch; do`

- [ ] **Step 3: Commit**

```bash
git add init-vault.sh
git commit -m "register fetch, hot, and playwright-fetch in init-vault.sh command loop"
```

---

## Task 5 — Update CLAUDE.md: session-start reflect check

**Files:**
- Modify: `CLAUDE.md:229-230`

- [ ] **Step 1: Replace rule #3 in the Session start section**

In `CLAUDE.md`, find and replace exactly:

Old:
```
3. If `wiki/compass.md` hasn't been updated in more days than
   `lint.reflect_reminder_days` (from `vault.config.yml`), suggest running `/reflect`.
```

New:
```
3. Read the `updated` field from `wiki/compass.md` frontmatter. If the file is
   absent or its `updated` date is more than `lint.reflect_reminder_days` days
   ago, suggest running `/reflect`.
```

- [ ] **Step 2: Verify**

```bash
grep -A2 "reflect_reminder_days" CLAUDE.md
```

Expected: shows "Read the \`updated\` field from \`wiki/compass.md\` frontmatter."

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "clarify reflect reminder: read compass.md updated frontmatter field"
```

---

## Task 6 — Update CLAUDE.md: session-end hot.md instruction

**Files:**
- Modify: `CLAUDE.md:214-216`

- [ ] **Step 1: Replace the Hot cache section body**

In `CLAUDE.md`, find and replace exactly:

Old:
```
At session end, if we touched meaningful content, update `wiki/hot.md`
with 5-10 lines on what we covered, what's open, what to pick up next.
Don't add — replace. At session start, read `wiki/hot.md` first.
```

New:
```
After any session in which `wiki/` was written to, run `/hot` before the
final response. "Written to" means any ingest, promote, view, reflect,
forget, or refresh that produced file changes — not queries.

`/hot` replaces the entire file. `wiki/log.md` is the append-only record;
`wiki/hot.md` is the current snapshot.
```

- [ ] **Step 2: Verify**

```bash
grep -A5 "## Hot cache" CLAUDE.md
```

Expected: shows "After any session in which \`wiki/\` was written to, run \`/hot\`"

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "tighten session-end hot.md instruction: reference /hot command, define written-to"
```

---

## Task 7 — Update CLAUDE.md: FORGET cascade step 5

**Files:**
- Modify: `CLAUDE.md:138-140`

- [ ] **Step 1: Replace FORGET step 5**

In `CLAUDE.md`, find and replace exactly:

Old:
```
5. Delete `wiki/sources/<slug>.md` and the `raw/` file. This is the
   one case where writing to `raw/` (as deletion) is allowed —
   invariant #1 covers creation, not user-directed removal.
```

New:
```
5. Delete `wiki/sources/<slug>.md`. Delete the entire raw folder:
   - Web sources: `raw/web/<slug>/` (includes `index.md` and `assets/`).
   - PDF sources: `raw/papers/<slug>/` (includes `paper.pdf` and `index.md`).

   This is the one case where writing to `raw/` (as deletion) is allowed —
   invariant #1 covers creation, not user-directed removal.
```

- [ ] **Step 2: Verify**

```bash
grep -A6 "5\. Delete" CLAUDE.md
```

Expected: shows both web and PDF raw folder paths with their contents listed.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "expand FORGET step 5: delete entire raw folder including assets subdirectory"
```

---

## Task 8 — Update `commands/ingest.md`: pre-ingest dedup check

**Files:**
- Modify: `commands/ingest.md`

- [ ] **Step 1: Insert pre-ingest check subsection**

In `commands/ingest.md`, find and replace exactly:

Old:
```
## Protocol

### Web articles
```

New:
```
## Protocol

### Pre-ingest check

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

### Web articles
```

- [ ] **Step 2: Verify**

```bash
grep -n "Pre-ingest\|Web articles\|PDFs" commands/ingest.md
```

Expected: "Pre-ingest check" appears before "Web articles".

- [ ] **Step 3: Commit**

```bash
git add commands/ingest.md
git commit -m "add pre-ingest deduplication check to /ingest protocol"
```

---

## Task 9 — Update `commands/refresh.md`: PDF branch protocol

**Files:**
- Modify: `commands/refresh.md`

- [ ] **Step 1: Replace steps 1–3 with branching protocol**

In `commands/refresh.md`, find and replace exactly:

Old:
```
1. **Resolve slug.** Find `wiki/sources/<slug>.md` and read `source_url`
   from its frontmatter. Confirm with the user: show title and source_url.

2. **Queue for re-fetch.** Add the URL back to `inbox.md` as an unchecked
   entry under "To process"
   (`inbox.md` is not under `raw/` — this write is permitted by invariant #1):
   ```
   - [ ] <source_url>
   ```
   Instruct the user to run the fetcher script to overwrite the raw folder:
   ```bash
   python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
   ```

3. **Re-ingest.** After the fetcher completes, rewrite `wiki/sources/<slug>.md`
   with a new summary from the updated raw content. Bump `updated` to today.
```

New:
```
1. **Resolve slug.** Find `wiki/sources/<slug>.md` and read `source_url`
   and `fetch_method` from its frontmatter. Confirm with the user:
   show title, source_url, and fetch_method.

2. **Branch by source type.**

   **Web article** (`fetch_method` absent or `html`):
   Add the URL back to `inbox.md` as an unchecked entry under "To process"
   (`inbox.md` is not under `raw/` — this write is permitted by invariant #1):
   ```
   - [ ] <source_url>
   ```
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

- [ ] **Step 2: Verify**

```bash
grep -n "fetch_method\|Re-summarise\|Branch by" commands/refresh.md
```

Expected: all three strings appear.

- [ ] **Step 3: Commit**

```bash
git add commands/refresh.md
git commit -m "add PDF branch to /refresh: ask before re-fetching unchanged papers"
```

---

## Task 10 — Update `vault-linter/SKILL.md`: check count, table, severity

**Files:**
- Modify: `skills/vault-linter/SKILL.md`

Three changes in one pass on the same file.

- [ ] **Step 1: Update the frontmatter description**

In `skills/vault-linter/SKILL.md`, find and replace exactly:

Old:
```
description: Runs deterministic health checks on a second brain wiki vault (dead links, orphan pages, duplicates, missing metadata, inconsistent naming, stale sources, gaps, view staleness, missing cross-references) and writes a report to .lint/report.md. Use this skill when the user says "lint", "check the vault", "vault health", "find broken links". Also run periodically — triggered when 5+ ingests have occurred since last lint OR 7+ days have passed. Supports unattended mode via --unattended flag. Fast, no LLM tokens consumed.
```

New:
```
description: Runs deterministic health checks on a second brain wiki vault (dead links, orphan pages, duplicates, missing metadata, inconsistent naming, stale sources, gaps, view staleness, missing cross-references, view based_on dead links, PDF index integrity, conversation schema, source index sync) and writes a report to .lint/report.md. Use this skill when the user says "lint", "check the vault", "vault health", "find broken links". Also run periodically — triggered when 5+ ingests have occurred since last lint OR 7+ days have passed. Supports unattended mode via --unattended flag. Fast, no LLM tokens consumed.
```

- [ ] **Step 2: Update the check count heading and extend the table**

In `skills/vault-linter/SKILL.md`, find and replace exactly:

Old:
```
Nine deterministic checks. Each produces findings with concrete paths.

| # | Check | What it catches |
|---|---|---|
| 1 | **Dead links** | `[[path]]` pointing to non-existent files |
| 2 | **Orphan pages** | Pages with zero incoming links (excluding hot.md, compass.md, index.md, views) |
| 3 | **Duplicate concepts** | Pages with similar titles within the same subdir |
| 4 | **Missing metadata** | Frontmatter missing required fields for the type |
| 5 | **Inconsistent naming** | Same concept referenced by different names |
| 6 | **Stale sources** | `wiki/sources/` pages not updated in >180 days |
| 7 | **Gaps** | Concept names in prose without a corresponding page |
| 8 | **View staleness** | Evolving views (`shareable: false`) whose `based_on` pages changed more than 30 days after |
| 9 | **Missing cross-references** | Source pages citing a page in prose without a link |
```

New:
```
Thirteen deterministic checks. Each produces findings with concrete paths.

| # | Check | What it catches |
|---|---|---|
| 1 | **Dead links** | `[[path]]` pointing to non-existent files |
| 2 | **Orphan pages** | Pages with zero incoming links (excluding hot.md, compass.md, index.md, views) |
| 3 | **Duplicate concepts** | Pages with similar titles within the same subdir |
| 4 | **Missing metadata** | Frontmatter missing required fields for the type |
| 5 | **Inconsistent naming** | Same concept referenced by different names |
| 6 | **Stale sources** | `wiki/sources/` pages not updated in >180 days |
| 7 | **Gaps** | Concept names in prose without a corresponding page |
| 8 | **View staleness** | Evolving views (`shareable: false`) whose `based_on` pages changed more than 30 days after |
| 9 | **Missing cross-references** | Source pages citing a page in prose without a link |
| 10 | **Based-on dead links** | `based_on` entries in view frontmatter pointing to non-existent pages |
| 11 | **PDF index integrity** | `raw/papers/` subdir missing `index.md`, or legacy flat `.pdf` in `raw/papers/` |
| 12 | **Conversation schema** | `conversations/` files missing `type: conversation` frontmatter field |
| 13 | **Source index sync** | `wiki/sources/` entry not mentioned in `wiki/index.md` |
```

- [ ] **Step 3: Update the severity notes**

In `skills/vault-linter/SKILL.md`, find and replace exactly:

Old:
```
- **Blocking** — dead links, missing required metadata.
- **Important** — orphans.
- **Advisory** — duplicates, stale, naming, view staleness, gaps, missing cross-references.
```

New:
```
- **Blocking** — dead links, missing required metadata, based-on dead links.
- **Important** — orphans.
- **Advisory** — duplicates, stale, naming, view staleness, gaps, missing cross-references, PDF index integrity, conversation schema, source index sync.
```

- [ ] **Step 4: Verify all three changes**

```bash
grep -n "Thirteen\|Based-on dead\|PDF index integrity\|conversation schema\|source index sync" skills/vault-linter/SKILL.md
```

Expected: all five strings appear.

- [ ] **Step 5: Commit**

```bash
git add skills/vault-linter/SKILL.md
git commit -m "update vault-linter SKILL.md: 13 checks, extended table and severity notes"
```

---

## Task 11 — Update `inbox-fetcher/SKILL.md`: Playwright pointer

**Files:**
- Modify: `skills/inbox-fetcher/SKILL.md:119-145`

- [ ] **Step 1: Replace the Playwright fallback section**

In `skills/inbox-fetcher/SKILL.md`, find and replace exactly:

Old:
```
## Playwright fallback

Any URL marked `⚠ ... — try playwright` in inbox.md is a hand-off from the script to the agent. The script never calls a browser; the agent uses the Playwright MCP (`mcp__plugin_playwright_playwright__browser_*`) interactively, one URL at a time.

**Protocol per URL:**

1. **Confirm with the user** before fetching. Never batch-process walled URLs unattended.
2. Navigate with `browser_navigate` to the URL.
3. If auth is required and the user is logged in (persistent profile), proceed. Otherwise stop and report — don't attempt to bypass auth.
4. Use `browser_snapshot` to get the accessibility tree, or `browser_evaluate` to extract the article/tweet text from the DOM. For X/Twitter threads, collect the full thread, not just the root post.
5. Generate a slug (title for articles; `<handle>-<tweet-id>` for X/Twitter).
6. Write `raw/web/<slug>/index.md` with frontmatter:
   ```yaml
   ---
   source_url: <url>
   title: <inferred or first-line-of-post>
   author: <handle or author>
   published: <YYYY-MM-DD if visible>
   fetched: <today>
   fetched_via: playwright
   ---
   ```
7. Save screenshots to `raw/web/<slug>/assets/` only if the user asks — they're large and rarely needed.
8. In `inbox.md`, move the line to `## Processati` with `- [x] <url> → \`raw/web/<slug>/\` (<today>)`. Remove the `⚠` marker.
9. Report to the user what was captured and ask whether to proceed to INGEST.

**Out of scope for the fallback:** bypassing login walls, solving CAPTCHAs, scraping at volume. If any of these come up, stop and tell the user.
```

New:
```
## Playwright fallback

Any URL marked `⚠ ... — try playwright` in inbox.md is a hand-off from
the script to the agent. Use the `/playwright-fetch` command — it contains
the full per-URL protocol.
```

- [ ] **Step 2: Verify**

```bash
grep -c "browser_navigate\|Protocol per URL" skills/inbox-fetcher/SKILL.md
```

Expected: `0` (old protocol lines are gone).

```bash
grep "playwright-fetch" skills/inbox-fetcher/SKILL.md
```

Expected: shows the pointer line.

- [ ] **Step 3: Commit**

```bash
git add skills/inbox-fetcher/SKILL.md
git commit -m "replace Playwright protocol in inbox-fetcher SKILL.md with pointer to /playwright-fetch"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|-----------------|------|
| §1 `commands/fetch.md` | Task 1 |
| §1 `commands/hot.md` | Task 2 |
| §1 `commands/playwright-fetch.md` | Task 3 |
| §1 `init-vault.sh` command loop | Task 4 |
| §2 Session-start reflect check (rule #3) | Task 5 |
| §2 Session-end hot.md instruction | Task 6 |
| §2 FORGET cascade step 5 | Task 7 |
| §3 `commands/ingest.md` dedup check | Task 8 |
| §3 `commands/refresh.md` PDF branch | Task 9 |
| §4 `vault-linter/SKILL.md` description, table, severity | Task 10 |
| §4 `inbox-fetcher/SKILL.md` Playwright pointer | Task 11 |

All 11 spec sections covered. No gaps.

**Placeholder scan:** No TBDs, TODOs, or "similar to above" shortcuts. Every step contains the exact replacement text.

**Consistency check:**
- `/playwright-fetch` referenced in Task 1 (fetch.md "After running" step 2), Task 3 (the command itself), Task 11 (SKILL.md pointer). ✓
- `/hot` referenced in Task 2 (the command itself), Task 6 (CLAUDE.md Hot cache body). ✓
- `fetch_method` read from `wiki/sources/<slug>.md` in Task 9 — that field is present on all sources per the existing ingest protocol. ✓
- `### Pre-ingest check` heading level (H3) matches all other subsection headings inside `## Protocol` in commands/ingest.md. ✓
