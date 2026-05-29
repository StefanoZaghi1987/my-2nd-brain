# Second Brain Vault 

A self-maintaining personal knowledge vault pattern, based on
[Andrej Karpathy's LLM Wiki idea](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

You curate sources. The agent compiles a wiki, answers your
questions, builds views when you ask, and periodically reflects on
where your thinking is going. Works with Claude Code, Codex, or any
agent that reads `CLAUDE.md` or `AGENTS.md`.

**→ Read [GETTING-STARTED.md](GETTING-STARTED.md) first.**

---

## What's in this project

```
vault-bundle/
├── init-vault.sh         bootstrap script — Unix/macOS/WSL
├── init_vault.py         bootstrap script — cross-platform (Linux, WSL, Windows)
├── vault.config.yml      per-vault tunable settings (timeouts, walled domains, lint thresholds)
├── CLAUDE.md             the contract between you and the agent
├── GETTING-STARTED.md    10-minute walkthrough for newcomers
├── README.md             this file
├── skills/
│   ├── inbox-fetcher/    URL → markdown in raw/ (web + PDFs); raw/drop/ adoption (PDFs and .md)
│   ├── vault-linter/     deterministic health checks (15 checks)
│   └── view-builder/     timelines, comparisons, charts, slides, reports, posts
├── commands/
│   ├── save.md               /save
│   ├── view.md               /view
│   ├── reflect.md            /reflect
│   ├── forget.md             /forget
│   ├── lint.md               /lint
│   ├── promote.md            /promote
│   ├── refresh.md            /refresh
│   ├── ingest.md             /ingest
│   ├── fetch.md              /fetch
│   ├── hot.md                /hot
│   └── playwright-fetch.md   /playwright-fetch
└── docs/examples/
    ├── research-example.md
    └── mealplan-example.md
```

---


## Quick start

```bash
git clone https://github.com/maeste/my-2nd-brain.git
cd my-2nd-brain
./init-vault.sh                    # → ./second-brain-vault  (Unix/macOS/WSL)
# or — cross-platform (Linux, WSL, Windows):
python3 init_vault.py              # → ./second-brain-vault
# or
python3 init_vault.py ~/knowledge/X      # explicit path
python3 init_vault.py --here             # current directory
```

Script is idempotent — safe to re-run.

Then open Claude Code (or another CLI) in the vault and follow
[GETTING-STARTED.md](GETTING-STARTED.md).

**To add a local file (no URL needed):** copy a PDF or Markdown file (`.md`) into
`raw/drop/` in your vault, then run `/ingest`. The agent adopts it into `raw/local/`
and summarises it.

### Updating an existing vault

Re-running the bootstrap script against an existing vault is the
update path. After `git pull` in this repo, re-run pointing at your vault:

```bash
./init-vault.sh ~/knowledge/X          # Unix/macOS/WSL
python3 init_vault.py ~/knowledge/X    # Windows / cross-platform
```

What happens on re-run:

- **Always refreshed** — `skills/`, `commands/`, and
  `skills/shared/vault_state.py`. This is the whole point of the
  update: new operations, fixes, and slash commands land in the vault.
- **Prompts you** — `CLAUDE.md`. Default is *keep* (answer `y` to
  overwrite with the latest template). Say yes unless you've
  customized the contract locally.
- **Created only if missing** — `vault.config.yml`, `inbox.md`,
  `wiki/index.md`, `wiki/log.md`, `wiki/hot.md`, `.lint/state.yaml`,
  `.gitignore`. Edit `vault.config.yml` to customise timeouts,
  walled domains, and lint thresholds.
- **Never touched** — `raw/`, `wiki/pages/`, `wiki/sources/`,
  `wiki/views/`, `conversations/`, `wiki/compass.md`. Your
  knowledge and ongoing work are safe.

No separate update script exists — both bootstrap scripts already do
the right thing on re-run.

---

## The core idea, in one paragraph

A directory `raw/` with immutable sources. An agent that compiles
them into a wiki of markdown pages. Queries against that wiki,
answered by the agent with citations. Views (timelines, comparisons,
slides) built on demand. A periodic `/reflect` that writes prose
about where your thinking is going. All of it evolves together — ask
Karpathy calls it *compounding*: every source you add, every
conversation you save, every view you build, increases what the next
question can draw on.

---

## Design principles

Six invariants:

1. **Raw is immutable.** If the wiki is corrupted, it's recompilable
   from `raw/` alone. Scripts (`fetch_inbox.py`, `adopt_drop.py`) write
   to `raw/` — the agent doesn't.
2. **Every claim cites a source.** No orphan claims in the wiki.
3. **Paraphrase, don't copy.** Summaries are in the agent's words.
4. **You curate, the agent maintains.** No auto-fetching, no
   auto-structural changes, no views without your request.
5. **`shareable: true` views are frozen.** Anything else evolves.
6. **Touch ≤15 files per operation.** If more are needed, stop and ask — split the work across sessions.

---

## Dependencies

**For `inbox-fetcher`** (Python):

```bash
pip install trafilatura requests python-slugify
```

> **Windows:** use `python` if `python3` is not recognised.

**For `vault-linter`** and **`view-builder`**:
Python standard library only. For charts (optional):

```bash
pip install matplotlib
```

**For the agent**: Claude Code, Codex, or any CLI that reads
`CLAUDE.md` / `AGENTS.md` and supports slash commands.

---

## Troubleshooting

**`python: command not found`** → install Python 3.10+.

**Inbox fetcher fails on some URLs** → likely paywall, JS-rendered, or
a walled domain (X/Twitter, LinkedIn, Threads, Facebook, Instagram).
The fetcher marks these `⚠ ... — try playwright` and leaves them
unchecked. Run `/playwright-fetch` — the agent will retrieve them
interactively via the Playwright MCP, one URL at a time, with your
confirmation per URL. Obsidian Web Clipper remains a manual fallback
if Playwright MCP is unavailable.

**Linter flags many orphan pages early on** → expected. Orphan check
becomes meaningful when the wiki has >50 pages. Views are
automatically exempt.

**`/reflect` has little to say** → probably not enough saved
conversations. Use `/save` more. Also needs a few weeks of activity
before the signals land.

**AGENTS.md not recognized** → replace the symlink with a copy:
`rm AGENTS.md && cp CLAUDE.md AGENTS.md`.

---

## Evolving the contract

`CLAUDE.md` is designed to co-evolve. When you hit friction, ask the
agent to propose a change. Good changes get committed; bad ones get
reverted. Your vault, your rules.

---

## License and attribution

MIT. Built on the pattern described by
[Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
