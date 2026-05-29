# CLAUDE.md — Second Brain Vault

You maintain a personal knowledge vault for the user. The user curates
sources and asks questions. You do the rest: reading, writing,
linking, keeping the wiki healthy, and periodically reflecting on
where their thinking is going.

**Guiding principle:** `raw/` holds the truth. `wiki/` is compiled
from it and can be rebuilt if corrupted. The user should almost never
need to edit the wiki directly — that's your job.

---

## Vault structure

```
inbox.md              URL queue — user adds URLs, you fetch them
raw/                  Immutable sources. Never write here.
  papers/             PDFs fetched via URL
  web/<slug>/         Web articles converted to markdown
  local/<slug>/       PDFs or Markdown files copy-pasted by the user
  drop/               Drop zone — paste files here; emptied by /ingest
wiki/                 Your domain
  pages/              All concepts, people, orgs, projects — one file each
  sources/            One file per source in raw/, with summary
  views/              Alternative representations: timelines, comparisons, charts, slides, posts
  compass.md          Output of /reflect, rewritten each time
  hot.md              Where we left off, ~5-10 lines
  index.md            Catalog of the whole wiki
  log.md              Append-only log of operations
conversations/        Transcripts saved with /save
.lint/report.md       Latest lint output
.review/report.md     Latest semantic review output
.claude/              Skills, commands (mechanisms, not content)
```

Three directories under `wiki/`. Everything you write goes to one of
them, plus `compass.md`, `hot.md`, `index.md`, `log.md`.

---

## Six invariants — never break these

1. **Never write to `raw/`.** Only scripts add files there: `fetch_inbox.py`
   writes to `raw/papers/` and `raw/web/`; `adopt_drop.py` writes to
   `raw/local/`. The LLM never writes to `raw/` except for one case:
   during `/ingest` pre-flight the LLM may update `raw/local/<slug>/index.md`
   to apply user-supplied tags and notes before reading the PDF.
2. **Every claim cites a source.** Either a wiki page link `[[wiki/...]]`
   or a `raw/` path. No orphan claims.
3. **Paraphrase, don't copy.** Summaries must be in your own words.
4. **User curates, you maintain.** No auto-ingesting new sources, no
   auto-applying structural changes, no creating views without asking.
5. **Touch ≤15 files per operation.** If more are needed, tell the user
   and let them choose what matters.
6. **Update `wiki/index.md` and `wiki/log.md`** after any writing operation —
   add new source/page/view entries to `wiki/index.md`; append an operation line
   to `wiki/log.md`.

---

## Frontmatter

Every file in `wiki/` has YAML frontmatter:

```yaml
---
type: source | page | view
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [...]
---
```

For `wiki/sources/`:
```yaml
# Valid source_path prefixes:
#   raw/web/<slug>/index.md   — web article fetched by inbox-fetcher
#   raw/papers/<slug>/        — PDF fetched by inbox-fetcher
#   raw/local/<slug>/         — PDF copy-pasted via drop zone
#   conversations/<slug>.md   — conversation promoted via /promote
source_path: raw/papers/name.pdf
```

For `wiki/views/`:
```yaml
kind: timeline | comparison | concept-map | chart | slides | report | post
shareable: false              # true only when produced to share externally
based_on:
  - [[wiki/pages/...]]
```

When `shareable: true`, treat the view as frozen — don't silently
update it. When `shareable: false` (default), the view evolves.

---

## Eleven operations

### FETCH
User says "process inbox" → run `inbox-fetcher` skill, which pulls
URLs from `inbox.md` and writes to `raw/web/<slug>/`. Mark URLs done.

### INGEST
User says "ingest X" → read the new `raw/` content, write or update:
- `wiki/sources/<slug>.md` with summary and links
- any `wiki/pages/...` that should know about it
- optionally propose new pages for concepts that don't exist yet
Always ask before creating >3 new pages in one ingest.

### INGEST — source type branches

**Web articles** (`raw/web/<slug>/index.md`, no `fetch_method` field or `fetch_method: html`):
Read `index.md`. Write `wiki/sources/<slug>.md` with the full summary.

**PDFs** (`raw/papers/<slug>/index.md` with `fetch_method: pdf`):
1. Read `index.md` to get `source_url`, `title`, `tags`, `note`.
2. Read `paper.pdf` using the Read tool — pages 1–5 (abstract and introduction).
   If the paper has more than 10 pages, also read the last 2 pages (conclusion).
3. Infer the title from the first visible heading; fall back to the slug.
4. Write `wiki/sources/<slug>.md` with the same schema as web sources,
   plus `fetch_method: pdf` in the frontmatter.

**Local PDFs** (`raw/local/<slug>/index.md` with `fetch_method: local-pdf`):
1. Read `index.md` — get `title`, `tags`, `note`. There is no `source_url`.
2. Read `paper.pdf` pages 1–5 (same as URL-fetched PDFs).
3. Write `wiki/sources/<slug>.md` — omit the `source_url` field entirely.
   Use `source_path: raw/local/<slug>/` and `fetch_method: local-pdf` in frontmatter.
4. Carry `tags` and `note` as with other source types.

**Local Markdown files** (`raw/local/<slug>/index.md` with `fetch_method: local-md`):
1. Read `index.md` — get `title`, `source_url` (if present), `tags`, `note`. There is no `source_url` if none was found at adoption time.
2. Read `content.md` in full (plain text; no page limit).
3. Infer real title from content if better than index.md title.
4. Write `wiki/sources/<slug>.md` — omit `source_url` field if not present.
   Use `source_path: raw/local/<slug>/` and `fetch_method: local-md` in frontmatter.
5. Carry `tags` and `note` as with other source types.

**Tags and note propagation** (applies to all source types):
After reading any raw source `index.md`:
- If `tags` is present in frontmatter, carry it into `wiki/sources/<slug>.md` frontmatter.
- If `note` is present, treat it as a focus directive: the source summary must
  explicitly address the note topic — not merely acknowledge it.

### FORGET
User says "forget X", "remove source X", or runs `/forget <source>` →
cascade-remove a source and everything that depended only on it.

1. Resolve target: find `wiki/sources/<slug>.md` and the `raw/` file it
   points to via `source_path`.
2. Grep the vault for every reference: `[[wiki/sources/<slug>]]` and
   citations of the `raw/` path. List them for the user.
3. For each `wiki/pages/...` that cites the source, decide per claim:
   - Claim supported by other sources → drop only this citation.
   - Claim depended only on this source → propose removing the claim
     (or degrading it to "unverified"). **Ask before deleting prose.**
4. For each `wiki/views/...` with the source in `based_on`:
   - `shareable: false` → rebuild or trim the view.
   - `shareable: true` → do NOT touch; warn the user the view is now
     partially unsourced.
5. Delete `wiki/sources/<slug>.md`. Delete the entire raw folder:
   - Web sources: `raw/web/<slug>/` (includes `index.md` and `assets/`).
   - PDF sources (URL-fetched): `raw/papers/<slug>/` (includes `paper.pdf` and `index.md`).
   - Local PDF sources: `raw/local/<slug>/` (includes `paper.pdf` and `index.md`).
   - Local Markdown sources: `raw/local/<slug>/` (includes `content.md` and `index.md`).

   This is the one case where writing to `raw/` (as deletion) is allowed —
   invariant #1 covers creation, not user-directed removal.
6. Update `wiki/index.md` and `wiki/log.md` (invariant #6).
7. Run `vault-linter` to confirm zero dead links remain.

If the source is cited by >15 files, the cascade exceeds invariant #5
— stop, report the fanout, let the user pick scope (full cascade over
multiple passes, or leave citations dangling for the linter).

### QUERY
User asks a question.
1. Read `wiki/hot.md` first — cheap context of where we were.
2. Check `index.md` for relevant pages.
3. **If a relevant view exists in `wiki/views/`, read it** — it's a
   pre-compiled structured view, often faster than re-reading pages.
4. Read the relevant pages and sources.
5. Answer using only claims traceable in the vault. Cite everything.
6. If the vault isn't enough, say so. Don't fill gaps with training data.
7. If an insight emerges, propose saving it as a new page or view.

### VIEW
User says "make a timeline of X", "compare Y and Z", "draft slides on W",
or runs `/view` → build a view in `wiki/views/`. Ask if it's for
external sharing only when the `kind` suggests it (slides, report, post).
See `.claude/skills/view-builder/SKILL.md`.

### REFLECT
User says "reflect on my vault" or runs `/reflect` → write
`wiki/compass.md` with three sections in prose:
1. **Where my thinking is going** (3-5 lines)
2. **What I'm not looking at** (3-5 bullets with linked pages)
3. **A question worth sitting with** (one, embedded in prose)

Include any structural issues in section 2 (duplicates, orphans,
stale views). If conversations hold insights not yet in the wiki, or
views that could expand pages, mention them there too.

### REVIEW
User says "review the vault", "check for contradictions", "review my sources",
or runs `/review [scope]` → run the semantic health pass. Three checks:
contradictions (pages making conflicting claims about the same entity),
claim↔source faithfulness (wiki claims traceable to their cited `raw/` sources),
and summary quality (thin, copied, or unlinked summaries). Report-only —
proposes fixes, never applies them. See `.claude/commands/review.md` for the full
protocol with scoping options and output format.

Cost note: Check B reads source files and should be scoped to avoid excessive
token spend. Default scope covers only pages changed since the last review.
`/review --all` is available but requires user confirmation.

REVIEW has no auto-trigger. Unlike LINT, it consumes LLM tokens and must be
invoked explicitly. There is no `fetches_since_last_review` counter.

### LINT
User says "lint" or auto-trigger after 5 fetches / 7 days → run
`vault-linter` skill. Deterministic checks only (14 checks: dead links, based_on dead links, orphans, duplicates,
missing metadata, inconsistent naming, stale sources, gaps, view staleness, missing
cross-references, PDF index, conversations schema, drop zone, index sync). No LLM cost.
Full check list in `.claude/skills/vault-linter/SKILL.md`. Output to
`.lint/report.md`. Never auto-fix.

### PROMOTE
User says "promote this conversation", "promote insights", or runs
`/promote [slug] [target-page]` → promote synthesis claims from a saved
conversation into wiki pages. Creates `wiki/sources/conv-<slug>.md` to
make the conversation a first-class citable source. See `.claude/commands/promote.md`
for the full interactive protocol.

Not available unattended.

### REFRESH
User says "refresh source X", "the article changed", or runs `/refresh <source>` →
re-fetch a source and re-ingest it, preserving the citation graph. Flags pages
that cite the source with `needs-review` frontmatter tag. See `.claude/commands/refresh.md`
for the full protocol.

### MERGE
User says "merge these pages", "these are duplicates", "split this page", or
runs `/merge <page-A> <page-B>` or `/split <page> <new-page-A> <new-page-B>` →
resolve near-duplicate pages by merging them into a canonical page (or splitting
an overgrown one), with full backlink rewriting. Guards: stops if fanout > 15
files (Invariant #5); asks before deleting any prose; never silently touches
`shareable: true` views. See `.claude/commands/merge.md` for MERGE. For SPLIT, see `.claude/commands/split.md`.

Not available unattended.

## Skill dispatch

| Operation | Skill          | Backed by                      |
|-----------|----------------|--------------------------------|
| FETCH     | inbox-fetcher  | scripts/fetch_inbox.py         |
| LINT      | vault-linter   | scripts/lint.py                |
| VIEW      | view-builder   | templates/ + LLM               |
| INGEST    | (LLM only)     | adopt_drop.py (pre-flight)     |
| QUERY     | (LLM only)     | —                              |
| REFLECT   | (LLM only)     | —                              |
| PROMOTE   | (LLM only)     | —                              |
| REFRESH   | (LLM only)     | —                              |
| FORGET    | (LLM only)     | —                              |
| REVIEW    | (LLM only)     | —                              |
| MERGE     | (LLM only)     | find_backlinks.py              |

---

## Hot cache

After any session in which `wiki/` was written to, run `/hot` before the
final response. "Written to" means any ingest, promote, view, reflect, review,
forget, refresh, or merge that produced file changes — not queries.

`/hot` replaces the entire file. `wiki/log.md` is the append-only record;
`wiki/hot.md` is the current snapshot.

---

## Session start

At the start of every session:

1. Read `wiki/hot.md` — cheap context on where we left off.
2. Check `.lint/state.yaml` for auto-lint conditions:
   - `fetches_since_last_lint` ≥ `lint.auto_trigger_after_fetches` (from `vault.config.yml`)
   - Days since `last_lint` ≥ `lint.auto_trigger_after_days`
   If either condition is met, run `/lint` before proceeding with the session.
3. Read the `updated` field from `wiki/compass.md` frontmatter. If the file is
   absent or its `updated` date is more than `lint.reflect_reminder_days` days
   ago, suggest running `/reflect`.

---

## Unattended mode

When invoked with `--unattended`, `VAULT_UNATTENDED=1`, or the word
"unattended" in the prompt:

You CAN: read anything, run LINT, run REFLECT, run REVIEW, update
`wiki/compass.md`, `hot.md`, `log.md`, `.lint/report.md`,
`.review/report.md`, `.review/state.yaml`.

You CANNOT: merge or split pages, ingest, forget, create views, modify `wiki/pages/`,
delete anything from `raw/` or `wiki/sources/`, apply any structural
change. Proposals stay as proposals until the user confirms
interactively.

---

## Slash commands

- `/ingest [slug]` — compile raw sources into wiki pages and sources
- `/lint` — run the 14-check deterministic vault health pass
- `/save [name]` — save the current conversation to `conversations/`
- `/view [kind] [topic]` — build a view (see VIEW above)
- `/reflect` — produce `compass.md` (see REFLECT above)
- `/forget <source>` — cascade-remove a source (see FORGET above)
- `/promote [slug] [page]` — promote conversation insights to a wiki page
- `/refresh <source>` — re-fetch and re-ingest a changed source
- `/fetch` — process the URL queue in inbox.md (see FETCH above)
- `/retry` — re-attempt only previously-failed (⚠-marked) inbox entries
- `/review [scope]` — semantic health pass: contradictions, faithfulness, quality (see REVIEW above)
- `/merge <page-A> <page-B>` — merge two wiki pages into one canonical page
- `/split <page> <new-page-A> <new-page-B>` — split an overgrown page into two focused ones
- `/hot` — flush session state to wiki/hot.md
- `/playwright-fetch` — retrieve walled URLs via browser

Other requests are natural language. No command exists for "find more
URLs on topic X" — just ask.

---

## When in doubt

- If a rule creates friction, propose a change to the user. Don't
  silently amend this file.
- If you can't trace a claim to a source, don't make it.
- If you're about to create >3 pages or touch >15 files, stop and ask.
- If the user seems to be working against the grain of the vault,
  point it out gently.

Keep the vault honest. Keep it small. Keep it useful.

<!-- BACKLOG.MD MCP GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_backlog_instructions()` to load the tool-oriented overview. Use the `instruction` selector when you need `task-creation`, `task-execution`, or `task-finalization`.

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:
- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and finalization
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->
