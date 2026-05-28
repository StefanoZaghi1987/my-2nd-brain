# Getting Started

Read this first. Ten minutes to the full picture.

---

## What this is

A personal knowledge vault, maintained by an AI agent, based on
[Andrej Karpathy's LLM Wiki idea](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

You curate sources. The agent reads them, compiles a wiki, answers
your questions, builds timelines and slides when you ask, and
periodically reflects on where your thinking is going.

The agent does the bookkeeping. You do the thinking.

---

## The whole thing in one diagram

```
┌─────────────┐
│  inbox.md   │  ← you add URLs here
└──────┬──────┘
       │ FETCH (agent pulls the URLs)
       ▼
┌─────────────┐
│   raw/      │  ← immutable sources (PDFs, web clips)
└──────┬──────┘
       │ INGEST (agent reads, writes summaries)
       ▼
┌──────────────────────────────────────┐
│  wiki/                               │
│    pages/     ← concepts, people,    │
│                 orgs, projects       │
│    sources/   ← one per raw source   │
│    views/     ← timelines, slides,   │
│                 charts, reports      │
│    compass.md ← written by /reflect  │
│    hot.md     ← where we left off    │
└───────┬──────────────────────────────┘
        │ QUERY (agent reads wiki to answer)
        │ VIEW  (agent builds alternative representations)
        ▼
  your questions,
  your outputs
```

Four directories, four types of file: `raw/`, `wiki/pages/`,
`wiki/sources/`, `wiki/views/`. That's the whole vault.

---

## The three types

| Type | Where | What it is |
|---|---|---|
| **source** | `wiki/sources/` | Summary of one raw file, with link back to `raw/` |
| **page** | `wiki/pages/` | A concept, person, organization, project — anything you'd have a wiki page for |
| **view** | `wiki/views/` | Alternative representation: timeline, comparison, concept map, chart, slides, report, post |

Views come in two flavors:

- **Evolving** (`shareable: false`, the default): lives in place,
  grows with your understanding, read by the agent when it answers
  your questions.
- **Frozen** (`shareable: true`): snapshot for external sharing
  (slides for a talk, a report for a client), not modified
  silently after creation.

---

## Nine operations

The agent knows how to do nine things. You trigger them in plain
language or with a slash command.

| # | Operation | How to trigger | What happens |
|---|---|---|---|
| 1 | **FETCH** | `/fetch` or *"process the inbox"* | URLs in `inbox.md` → `raw/web/` or `raw/papers/<slug>/` |
| 2 | **INGEST** | `/ingest` or *"ingest the new content"* | `raw/` → summaries in `wiki/sources/`, links in `wiki/pages/` |
| 3 | **FORGET** | `/forget <source>` or *"forget source X"* | Cascade-remove a source, clean citations in pages and views |
| 4 | **QUERY** | any question | Agent reads the wiki, answers with citations |
| 5 | **VIEW** | `/view timeline agent-skills` or *"make a timeline of X"* | Build a view in `wiki/views/` |
| 6 | **REFLECT** | `/reflect` or *"reflect on my vault"* | Writes `wiki/compass.md` with trajectory + blind spots |
| 7 | **LINT** | `/lint` or automatic after 5 ingests / 7 days | Deterministic checks, report in `.lint/` |
| 8 | **PROMOTE** | `/promote [slug] [page]` or *"promote this conversation"* | Synthesis claims from a saved conversation → wiki pages |
| 9 | **REFRESH** | `/refresh <source>` or *"the article changed"* | Re-fetch a changed source, re-ingest, flag affected pages |

---

## Eleven slash commands

- **`/fetch`** — process the URL queue in `inbox.md`. Run this before
  `/ingest` — ingest needs the raw files that fetch downloads.
- **`/ingest [slug]`** — compile raw sources into the wiki. Without a
  slug, discovers all uningested sources and confirms before starting.
- **`/playwright-fetch`** — retrieve walled, paywalled, or JS-rendered
  URLs that `/fetch` couldn't download. One URL at a time, with your
  confirmation per URL.
- **`/save [name]`** — save the current conversation to
  `conversations/`. These feed `/reflect` and `/promote` later.
- **`/view [kind] [topic]`** — build a view. Kinds: `timeline`,
  `comparison`, `concept-map`, `chart`, `slides`, `report`, `post`.
- **`/reflect`** — write `compass.md`: where my thinking is going,
  what I'm not looking at, one question worth sitting with.
- **`/forget <source>`** — cascade-remove a source. Interactive:
  per-claim decisions, never deletes prose without asking.
- **`/lint`** — run deterministic vault health checks. Also triggers
  automatically after 5 ingests or 7 days.
- **`/promote [slug] [page]`** — lift synthesis claims from a saved
  conversation into a wiki page, with full citation. Interactive only.
- **`/refresh <source>`** — re-fetch a source whose content has
  changed, re-ingest it, and flag pages that may need review.
- **`/hot`** — flush session state to `wiki/hot.md`. The agent runs
  this automatically at the end of any writing session.

For everything else, just ask in plain language.

---

## First week

**Day 1: bootstrap.** Run `./init-vault.sh`. Add 5-10 URLs to
`inbox.md`. Tell the agent: *"process the inbox, then ingest the new
content"*. You'll have your first few pages and sources.

Tip: annotate URLs with optional sub-bullets before fetching — the
agent carries them through into the wiki summary:

```markdown
- [ ] https://arxiv.org/abs/2405.12345
  - tags: llm, agents
  - note: focus on the evaluation section
```

**Day 2-3: ask questions.** The wiki is small but already useful.
Ask things that require synthesis across sources. Notice when the
agent proposes new connections — those are the value.

**Day 4-5: add more sources.** Let it grow to 15-20 sources. The
ingest phase gets interesting when the wiki is populated — the agent
starts spotting links you didn't see.

**Day 6: save a good conversation.** When a session produces a
useful synthesis, `/save`. These conversations will feed `/reflect`
in a week or two.

**Day 7: `/reflect` for the first time.** Probably not much to say
yet. That's fine. Come back in a week.

---

## First month

**Week 2:** first real `/reflect`. The compass tells you where you're
going and what you're missing. Act on one of the suggestions.

**Week 3:** build your first `/view`. Most likely a timeline or a
comparison of something you've been accumulating sources on. This is
where the wiki shifts from "stored content" to "structured
understanding".

**Week 4:** the second-brain effect kicks in. You'll notice that
questions you ask are answered with connections you didn't set up
manually — the agent is reading your pages and views together,
compounding. Karpathy calls this *compounding*, and this is when you
see it.

---

## Six rules the agent follows

These are invariants. The agent won't break them. Good to know they
exist:

1. **`raw/` is immutable.** The agent never writes there directly.
2. **Every claim cites a source.** No orphan claims in the wiki.
3. **Paraphrase, don't copy.** Summaries are in the agent's words.
4. **You curate, it maintains.** No auto-fetching, no silent
   structural changes, no views without your request.
5. **`shareable: true` views are frozen.** New version = new dated
   file. Everything else can evolve in place.
6. **Touch ≤15 files per operation.** If more are needed, the agent
   stops and asks — split across sessions.

---

## What to read next

- **`CLAUDE.md`** — the full contract the agent follows. Worth reading
  once to understand how the agent makes decisions.
- **`docs/examples/research-example.md`** — a canonical research
  use case with annotated walkthrough.
- **`docs/examples/mealplan-example.md`** — same pattern applied to
  a non-research domain, to see the range.

---

## Common questions

**"Do I need to learn any syntax?"** No. Everything works in plain
language. Slash commands are shortcuts, not requirements.

**"How much should I customize CLAUDE.md?"** Probably nothing for the
first month. Use the default contract, see what friction you hit,
then adjust.

**"What if the agent does something I don't want?"** Tell it. The
agent is explicitly designed to ask before doing anything structural.
If it did something unasked, that's a contract violation and worth
noting in `CLAUDE.md` as a new rule.

**"Can I use this with an agent other than Claude?"** Yes. The vault
uses plain markdown. The contract is in `CLAUDE.md` / `AGENTS.md`
(symlinked for compatibility). Any CLI that reads one of those
should work.

**"Do I need Obsidian?"** No, but it helps. The vault is markdown
files with `[[wiki-links]]` — Obsidian renders them natively.
`init-vault.sh` creates `.obsidian/app.json` with `useMarkdownLinks:
false`, which keeps Obsidian writing `[[wikilinks]]` rather than
`[text](path)` links (the linter needs wikilink syntax to track links).
Other markdown editors work too.
