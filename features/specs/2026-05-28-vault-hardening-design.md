# Vault Hardening Design

**Date:** 2026-05-28
**Scope:** Bug fixes, linter enhancements, documentation gaps, agent protocol improvements, Obsidian skeleton

---

## Context

This spec follows the vault-improvements cycle (TASK-0001–0020, all complete). The vault's
foundation — config layer, shared state, PDF folder structure, tags/note propagation, nine
operations, skill manifests — is solid. This cycle hardens what's there: fixes five bugs
found during deep analysis, adds three linter checks, fills the INGEST command gap, makes
the session lifecycle explicit in CLAUDE.md, and adds a minimal Obsidian config.

**Main goal:** hardening, not extension. Every item here makes the existing design more
correct or more complete — no new architectural concepts introduced.

---

## Wave 1 — Code + Tests

All Wave 1 changes are in Python. Every change has pytest coverage. Wave 1 can be
parallelized: fetch changes and linter changes are independent.

---

### 1.1 Bug Fix — `update_inbox` orphans sub-bullets on success

**File:** `skills/inbox-fetcher/scripts/fetch_inbox.py`

**Root cause:** `update_inbox()` iterates `for line in lines:`. When a URL with
`- tags:` / `- note:` sub-bullets succeeds, the URL line is removed but sub-bullets
(which don't match `UNCHECKED_PATTERN`) pass through to `out_lines` as orphaned content.

**Fix:** Convert to `while i < len(lines):` with explicit index. Calculate sub-bullet
extent (`j`) upfront for every URL line, then branch:

- **Success:** drop sub-bullets (captured in raw frontmatter — no longer needed).
- **Failure:** keep sub-bullets under the ⚠ line (useful context for retry).
- **Not in this batch:** keep URL + sub-bullets unchanged.

```python
def update_inbox(inbox_path, inbox_text, results, processed_section="## Processed"):
    lines = inbox_text.splitlines()
    today = date.today().isoformat()
    result_by_url = {r.url: r for r in results}
    new_processed_lines = []
    out_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        match = UNCHECKED_PATTERN.match(line)
        if not match:
            out_lines.append(line)
            i += 1
            continue

        url = match.group(1).strip()

        # Determine sub-bullet extent
        j = i + 1
        while j < len(lines) and (lines[j].startswith(" ") or lines[j].startswith("\t")):
            j += 1

        if url not in result_by_url:
            out_lines.extend(lines[i:j])
            i = j
            continue

        result = result_by_url[url]
        if result.ok:
            new_processed_lines.append(
                f"- [x] {url} → `{result.out_path}` ({today})"
            )
            # sub-bullets captured in raw frontmatter — drop them
        else:
            out_lines.append(f"- [ ] {url} ⚠ {result.reason}")
            # keep sub-bullets for retry context
            out_lines.extend(lines[i + 1:j])

        i = j

    # ... processed_section header + append logic unchanged
```

**New tests in `tests/test_fetch_inbox.py`:**

```python
class TestUpdateInboxSubBullets:
    def test_successful_url_drops_sub_bullets(self):
        inbox = (
            "## To process\n"
            "- [ ] https://example.com/article\n"
            "  - tags: ai, llm\n"
            "  - note: read carefully\n"
        )
        results = [FetchResult(
            url="https://example.com/article", ok=True, kind="html",
            out_path=Path("raw/web/article/"),
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "tags: ai" not in new_text
        assert "note: read" not in new_text
        assert "- [x] https://example.com/article" in new_text

    def test_failed_url_keeps_sub_bullets(self):
        inbox = (
            "## To process\n"
            "- [ ] https://paywall.com/article\n"
            "  - tags: ai\n"
            "  - note: important\n"
        )
        results = [FetchResult(
            url="https://paywall.com/article", ok=False, kind="failed",
            reason="extraction empty — try playwright",
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "- [ ] https://paywall.com/article ⚠" in new_text
        assert "tags: ai" in new_text
        assert "note: important" in new_text

    def test_unprocessed_url_keeps_sub_bullets(self):
        inbox = (
            "## To process\n"
            "- [ ] https://example.com/other\n"
            "  - tags: other\n"
        )
        # Empty results — URL not in batch
        new_text = update_inbox(Path("dummy"), inbox, [],
                                processed_section="## Processed")
        assert "- [ ] https://example.com/other\n" in new_text
        assert "tags: other" in new_text
```

---

### 1.2 Bug Fix — `pdf_enabled` config key not enforced

**File:** `skills/inbox-fetcher/scripts/fetch_inbox.py`

**Root cause:** `cfg["fetch"]["pdf_enabled"]` is loaded but never read. Setting it to
`false` has no effect.

**Fix:** In `process_vault()`, check `pdf_enabled` before calling `fetch_pdf()`. Pattern
mirrors walled domains: produce a `FetchResult(ok=False)` with a clear reason, leave the
inbox line unchecked so the user can process manually.

```python
if is_pdf_url(fetch_url):
    if not cfg["fetch"]["pdf_enabled"]:
        r = FetchResult(
            url=fetch_url, ok=False, kind="failed",
            reason="PDF fetch disabled (pdf_enabled: false in vault.config.yml)",
        )
    else:
        r = fetch_pdf(fetch_url, papers_dir, slug_override=slug_override,
                      pdf_timeout=pdf_timeout, max_pdf_mb=max_pdf_mb,
                      tags=e.tags, note=e.note)
```

**New test:**

```python
class TestPdfEnabled:
    def test_pdf_skipped_when_disabled(self, tmp_path):
        from fetch_inbox import process_vault
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  pdf_enabled: false\n"
        )
        (tmp_path / "inbox.md").write_text(
            "- [ ] https://arxiv.org/pdf/2405.12345.pdf\n"
        )
        (tmp_path / "raw" / "papers").mkdir(parents=True)
        (tmp_path / "raw" / "web").mkdir(parents=True)
        process_vault(tmp_path)
        inbox_text = (tmp_path / "inbox.md").read_text()
        assert "⚠" in inbox_text
        assert "pdf_enabled" in inbox_text
        assert not list((tmp_path / "raw" / "papers").iterdir())
```

---

### 1.3 Extension — Content-Type header detection for PDF routing

**File:** `skills/inbox-fetcher/scripts/fetch_inbox.py`

**Root cause:** `is_pdf_url()` checks URL path suffix only. A URL like
`https://example.com/download?id=42` serving a PDF routes to trafilatura, which
returns empty, marking the URL as a failed fetch requiring playwright intervention —
when it should have been fetched as a PDF.

**Fix:** New helper function:

```python
def get_content_type(url: str, timeout: int = 10) -> str:
    """Probe a URL with a HEAD request; return Content-Type or '' on failure."""
    try:
        r = requests.head(
            url, timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        return r.headers.get("Content-Type", "")
    except Exception:
        return ""
```

Updated decision order in `process_vault()`:

```
1. is_pdf_url(fetch_url)                              → fetch_pdf  (suffix match, no HEAD)
2. is_walled(fetch_url, walled)                       → walled failure
3. "application/pdf" in get_content_type(fetch_url)   → fetch_pdf  (new, HEAD request)
4. else                                               → fetch_html
```

The HEAD request only fires when the URL doesn't already have a `.pdf` suffix (step 1
short-circuits). Servers returning 405 or timeouts fall through silently to `fetch_html`.

**New test:**

```python
class TestContentTypeRouting:
    def test_pdf_routed_by_content_type(self, tmp_path, requests_mock):
        from fetch_inbox import process_vault
        (tmp_path / "inbox.md").write_text(
            "- [ ] https://example.com/download?id=42\n"
        )
        (tmp_path / "raw" / "papers").mkdir(parents=True)
        (tmp_path / "raw" / "web").mkdir(parents=True)
        requests_mock.head(
            "https://example.com/download?id=42",
            headers={"Content-Type": "application/pdf"},
        )
        requests_mock.get(
            "https://example.com/download?id=42",
            content=b"%PDF-1.4 fake content",
        )
        process_vault(tmp_path)
        inbox_text = (tmp_path / "inbox.md").read_text()
        assert "[x]" in inbox_text
        assert any((tmp_path / "raw" / "papers").iterdir())
```

---

### 1.4 Bug Fix — `ORPHAN_EXCEPTIONS` dead entries

**File:** `skills/vault-linter/scripts/lint.py`

`load_wiki()` stores paths as `md_file.relative_to(vault).as_posix()`, which always
produces `wiki/index.md`, `wiki/log.md`, etc. The bare entries `"index.md"` and
`"log.md"` in `ORPHAN_EXCEPTIONS` never match anything.

**Fix:** Remove the two dead entries:

```python
ORPHAN_EXCEPTIONS = {
    "wiki/hot.md",
    "wiki/compass.md",
    "wiki/index.md",
    "wiki/log.md",
}
```

No new tests — existing orphan tests remain green. This is a correctness fix with no
behavioral change (the entries were unreachable).

---

### 1.5 Linter Enhancement — Conversation schema check

**File:** `skills/vault-linter/scripts/lint.py`

**New function `check_conversations(vault: Path) -> list[Finding]`** scans
`conversations/*.md` for structural issues. Two advisory checks:

1. `missing_conversation_type` — file lacks `type: conversation` frontmatter field.
   Advisory (not blocking) — existing conversations are grandfathered.
2. Age-based unpromoted check: **not included** — `/reflect` already handles this as a
   knowledge-lifecycle signal. The linter stays focused on structural health.

```python
def check_conversations(vault: Path) -> list[Finding]:
    """Check that conversation files have type: conversation frontmatter."""
    findings = []
    conv_dir = vault / "conversations"
    if not conv_dir.is_dir():
        return findings

    for md_file in conv_dir.glob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(text)
        if fm.get("type") != "conversation":
            findings.append(Finding(
                severity="advisory",
                check="missing_conversation_type",
                file=str(md_file.relative_to(vault)),
                detail="missing 'type: conversation' frontmatter field",
            ))
    return findings
```

Registered in `run_lint()` with the `fn(vault)` dispatcher branch alongside
`check_pdf_index`:

```python
elif name in ("pdf_index", "conversations"):
    out = fn(vault)
```

**New tests:**

```python
class TestCheckConversations:
    def test_no_findings_for_absent_conversations_dir(self, tmp_path):
        from lint import check_conversations
        assert check_conversations(tmp_path) == []

    def test_no_findings_when_type_present(self, tmp_path):
        conv = tmp_path / "conversations"
        conv.mkdir()
        (conv / "2026-05-01-session.md").write_text(
            "---\ntype: conversation\ndate: 2026-05-01\n---\n## Question\nWhat?\n"
        )
        from lint import check_conversations
        assert check_conversations(tmp_path) == []

    def test_advisory_for_missing_type(self, tmp_path):
        conv = tmp_path / "conversations"
        conv.mkdir()
        (conv / "2026-05-01-session.md").write_text(
            "---\ndate: 2026-05-01\n---\n## Question\nWhat?\n"
        )
        from lint import check_conversations
        findings = check_conversations(tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "missing_conversation_type"
        assert findings[0].severity == "advisory"
```

---

### 1.6 Linter Enhancement — `check_index_sync`

**File:** `skills/vault-linter/scripts/lint.py`

**New function `check_index_sync(pages: dict, vault: Path) -> list[Finding]`** verifies
that every `wiki/sources/<slug>.md` has a corresponding mention in `wiki/index.md`.

Logic:
1. If `wiki/index.md` is absent → return `[]` (vault is new, nothing to check).
2. Read index body text.
3. For each `wiki/sources/<slug>.md`: check if the slug string appears anywhere in the
   index body. This covers `[[wiki/sources/slug]]`, `[[wiki/sources/slug|Label]]`, and
   plain slug mentions.
4. Advisory finding if not found.

```python
def check_index_sync(pages: dict[str, WikiPage], vault: Path) -> list[Finding]:
    """Verify that every wiki/sources/ entry appears in wiki/index.md."""
    index_page = pages.get("wiki/index.md")
    if not index_page:
        return []

    index_text = index_page.body_text
    findings = []
    for rel, page in pages.items():
        if not rel.startswith("wiki/sources/"):
            continue
        slug = Path(rel).stem
        if slug not in index_text:
            findings.append(Finding(
                severity="advisory",
                check="index_sync",
                file=rel,
                detail="source not mentioned in wiki/index.md",
            ))
    return findings
```

Registered in `run_lint()` with its own dispatcher branch (needs both `pages` and `vault`):

```python
elif name in ("dead_links", "orphans", "based_on_dead_links", "index_sync"):
    out = fn(pages, vault)
```

**New tests:**

```python
class TestCheckIndexSync:
    def test_no_findings_when_index_absent(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/sources/agent-skills.md": (
                "---\ntype: source\nsource_path: raw/web/agent-skills/index.md\n"
                "created: 2026-01-01\nupdated: 2026-01-01\n---\n# Agent Skills\n"
            ),
        })
        from lint import load_wiki, check_index_sync
        pages = load_wiki(tmp_path)
        assert check_index_sync(pages, tmp_path) == []

    def test_no_findings_when_source_listed(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/sources/agent-skills.md": (
                "---\ntype: source\nsource_path: raw/web/agent-skills/index.md\n"
                "created: 2026-01-01\nupdated: 2026-01-01\n---\n# Agent Skills\n"
            ),
            "wiki/index.md": "# Index\n\n- [[wiki/sources/agent-skills]]\n",
        })
        from lint import load_wiki, check_index_sync
        pages = load_wiki(tmp_path)
        assert check_index_sync(pages, tmp_path) == []

    def test_advisory_when_source_missing_from_index(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/sources/agent-skills.md": (
                "---\ntype: source\nsource_path: raw/web/agent-skills/index.md\n"
                "created: 2026-01-01\nupdated: 2026-01-01\n---\n# Agent Skills\n"
            ),
            "wiki/index.md": "# Index\n\n## Sources\n\n<!-- empty -->\n",
        })
        from lint import load_wiki, check_index_sync
        pages = load_wiki(tmp_path)
        findings = check_index_sync(pages, tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "index_sync"
        assert findings[0].severity == "advisory"
```

---

### 1.7 Config Addition — `lint.reflect_reminder_days`

**Files:** `vault.config.yml`, `skills/shared/vault_state.py`

New key in the `lint` section:

**`vault.config.yml`:**
```yaml
lint:
  stale_source_days: 180
  view_stale_days: 30
  auto_trigger_after_ingests: 5
  auto_trigger_after_days: 7
  reflect_reminder_days: 14        # suggest /reflect after this many days without one
```

**`vault_state.py` `_DEFAULTS`:**
```python
"lint": {
    "stale_source_days": 180,
    "view_stale_days": 30,
    "auto_trigger_after_ingests": 5,
    "auto_trigger_after_days": 7,
    "reflect_reminder_days": 14,   # ← new
},
```

No new tests required — `TestLoadConfig` already covers config parsing and default
merging; a single additional assertion in an existing test is sufficient:

```python
# In TestLoadConfig.test_returns_all_default_sections_when_absent:
assert config["lint"]["reflect_reminder_days"] == 14
```

---

## Wave 2 — Documentation & Agent Protocols

All Wave 2 changes are prose and configuration. No Python logic, no tests. Can be
reviewed in a single reading pass.

---

### 2.1 Bug Fix — SKILL.md inbox-fetcher stale text

**File:** `skills/inbox-fetcher/SKILL.md`

In the `## Inbox format` section, replace:

> Indented sub-bullets (tags, notes) are preserved but not parsed — they're hints for
> the ingest step.

With:

> Indented sub-bullets (`- tags: tag1, tag2` and `- note: focus on X`) are parsed by
> the script and written into the raw source's `index.md` frontmatter. The ingest step
> reads them from there via tag/note propagation.

---

### 2.2 Bug Fix — SKILL.md vault-linter `gaps` severity mismatch

**File:** `skills/vault-linter/SKILL.md`

In the `## Output` → `.lint/report.md` section, change:

```
- **Important** — orphans, gaps.
- **Advisory** — duplicates, stale, naming, view staleness.
```

To:

```
- **Important** — orphans.
- **Advisory** — duplicates, stale, naming, view staleness, gaps, missing cross-references.
```

The code emits `severity="advisory"` for gaps (correct, given ~30% false positive rate).
The SKILL.md was wrong.

---

### 2.3 Bug Fix — README lists five invariants instead of six

**File:** `README.md`

In the `## Design principles` section, change heading from "Five invariants:" to
"Six invariants:" and add the missing sixth:

> 6. **Touch ≤15 files per operation.** If more files are needed, stop and ask — split
>    the operation across sessions.

---

### 2.4 New Command — `commands/ingest.md`

**File:** `commands/ingest.md` (new)

INGEST is the agent's primary write operation but has no slash command file. A new
conversation can reconstruct FETCH and LINT from skill files but has no equivalent
entry point for INGEST. The command file is a compact protocol sheet — not as elaborate
as `/forget`, which needs a defensive cascade protocol.

```markdown
---
description: Compile raw sources into the wiki. Reads raw/web/ and raw/papers/ for
  sources that don't yet have a wiki/sources/<slug>.md entry, summarises each, links
  them into wiki/pages/, and updates wiki/index.md and wiki/log.md.
---

# /ingest — Compile raw sources into the wiki

## When to use

After running the inbox fetcher (`/fetch` or the inbox-fetcher skill), or when new
files have been added to `raw/` manually. Also when asked to "ingest", "summarise
the new sources", or "add this to the wiki".

## Discover targets

If no slug is given: scan `raw/web/` and `raw/papers/` for subdirectories that have
an `index.md` but no corresponding `wiki/sources/<slug>.md`. These are the uningested
sources.

If a slug is given (`/ingest arxiv-2405-12345`): target that source only.

Confirm with the user before ingesting more than one source at a time:
> "Found N new sources: [list]. Ingest all?"

## Protocol

### Web articles

Source: `raw/web/<slug>/index.md` (no `fetch_method` field, or `fetch_method: html`).

1. Read `index.md` — get `source_url`, `title`, `tags`, `note`.
2. Read the article body.
3. Write `wiki/sources/<slug>.md` with a summary (paraphrase, not copy).
4. Propagate `tags` and treat `note` as a focus directive (see CLAUDE.md §INGEST).

### PDFs

Source: `raw/papers/<slug>/index.md` with `fetch_method: pdf`.

1. Read `index.md` — get `source_url`, `title`, `tags`, `note`.
2. Read `paper.pdf` — pages 1–5. If > 10 pages, also read the last 2.
3. Infer title from first heading; fall back to slug.
4. Write `wiki/sources/<slug>.md` with the same schema as web sources,
   plus `fetch_method: pdf` in frontmatter.
5. Propagate `tags` and `note` as above.

## Guards

- **≤3 new pages before confirm.** If ingesting a source would require creating
  more than 3 new `wiki/pages/` entries for emerging concepts, stop and list the
  proposed pages. Ask: "Create all three?" before writing any.
- **≤15 files per operation (invariant #5).** If a single ingest would touch more
  than 15 files, split across sessions. Report the count and ask which sources to
  prioritise.

## Completion steps

After every ingest (regardless of how many sources):

1. Update `wiki/index.md` — add a line under `## Sources` for each new source.
2. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <slug>` for each source.
3. Report to the user: sources ingested, pages created/updated, any guards triggered.
```

**`init-vault.sh`:** extend the command install loop:

```bash
for cmd in save view reflect forget lint promote refresh ingest; do
```

---

### 2.5 Agent Protocol — Session-start section in CLAUDE.md

**File:** `CLAUDE.md`

New section `## Session start` inserted between `## Hot cache` and `## Unattended mode`:

```markdown
## Session start

At the start of every session:

1. Read `wiki/hot.md` — cheap context on where we left off.
2. Check `.lint/state.yaml` for auto-lint conditions:
   - `ingests_since_last_lint` ≥ `lint.auto_trigger_after_ingests` (from `vault.config.yml`)
   - Days since `last_lint` ≥ `lint.auto_trigger_after_days`
   If either condition is met, run `/lint` before proceeding with the session.
3. If `wiki/compass.md` hasn't been updated in more days than
   `lint.reflect_reminder_days` (from `vault.config.yml`), suggest running `/reflect`.
```

This makes the session lifecycle explicit in CLAUDE.md — not merely documented in
`commands/lint.md` where a fresh conversation might not see it.

---

### 2.6 Schema Addition — Conversation frontmatter in `/save`

**File:** `commands/save.md`

Add `type: conversation` to the frontmatter template:

```markdown
## Template

​```markdown
---
type: conversation
date: YYYY-MM-DD
tags: [tag1, tag2]
pages_read:
  - [[wiki/pages/x]]
pages_written:
  - [[wiki/pages/x]]
views_used:
  - [[wiki/views/timeline-y]]
promoted_to: []
---
```

The `type: conversation` field enables the new linter check (§1.5). The `promoted_to`
field is populated by `/promote` and consulted by `/reflect`. Existing conversations
without `type: conversation` produce advisory-only linter findings — no migration
required.

---

### 2.7 Obsidian — Minimal skeleton in `init-vault.sh`

**File:** `init-vault.sh`

Add `.obsidian/` to the `DIRS` array:

```bash
DIRS=(
    ...
    ".obsidian"
)
```

After the `.gitignore` block, add `.obsidian/app.json` creation (skip if exists):

```bash
# --- Obsidian config ---------------------------------------------------
if [ ! -f "$VAULT_DIR/.obsidian/app.json" ]; then
    cat > "$VAULT_DIR/.obsidian/app.json" <<'EOF'
{
  "useMarkdownLinks": false,
  "newLinkFormat": "relative",
  "readableLineLength": true,
  "attachmentFolderPath": "wiki/views/assets"
}
EOF
    ok ".obsidian/app.json (useMarkdownLinks: false — required for vault link integrity)"
else
    skip ".obsidian/app.json (exists — keeping user config)"
fi
```

`useMarkdownLinks: false` is the critical field — it keeps Obsidian writing `[[wikilinks]]`
rather than `[text](path)` syntax, which would produce links the linter cannot track.
The existing `.gitignore` template already excludes `.obsidian/workspace*` and
`.obsidian/cache`; no change needed there.

---

### 2.8 CLAUDE.md — Invariant #6 sharpened

**File:** `CLAUDE.md`

In the `## Six invariants` section, sharpen invariant #6:

From:
> 6. **Update `index.md` and `log.md`** after any writing operation.

To:
> 6. **Update `wiki/index.md` and `wiki/log.md`** after any writing operation —
>    add new source/page/view entries to `wiki/index.md`; append an operation line
>    to `wiki/log.md`.

The full path (`wiki/`) removes ambiguity; the inline clarification of what "update"
means removes the gap that prompted the `check_index_sync` linter check.

---

## File Summary

### Wave 1 — Modified

| File | Changes |
|------|---------|
| `skills/inbox-fetcher/scripts/fetch_inbox.py` | §1.1 sub-bullet fix, §1.2 pdf_enabled, §1.3 content-type detection |
| `skills/vault-linter/scripts/lint.py` | §1.4 ORPHAN_EXCEPTIONS, §1.5 check_conversations, §1.6 check_index_sync |
| `vault.config.yml` | §1.7 reflect_reminder_days |
| `skills/shared/vault_state.py` | §1.7 reflect_reminder_days default |
| `tests/test_fetch_inbox.py` | §1.1, §1.2, §1.3 tests |
| `tests/test_lint.py` | §1.5, §1.6 tests; §1.7 assertion |
| `tests/test_vault_state.py` | §1.7 assertion |

### Wave 2 — Modified

| File | Changes |
|------|---------|
| `skills/inbox-fetcher/SKILL.md` | §2.1 stale text fix |
| `skills/vault-linter/SKILL.md` | §2.2 gaps severity fix |
| `README.md` | §2.3 six invariants |
| `CLAUDE.md` | §2.5 session-start section, §2.8 invariant #6 |
| `commands/save.md` | §2.6 type:conversation + promoted_to template |
| `init-vault.sh` | §2.4 ingest command loop, §2.7 Obsidian skeleton |

### Wave 2 — Created

| File | Changes |
|------|---------|
| `commands/ingest.md` | §2.4 new /ingest command |

---

## Invariants — unchanged

All six vault invariants remain intact. §2.8 sharpens the wording of #6 without
changing its meaning. No new invariants introduced.

---

## Backlog task summary

| Wave | Items | Description |
|------|-------|-------------|
| Wave 1 | 7 items | fetch fixes, linter enhancements, config key |
| Wave 2 | 8 items | doc fixes, new command, CLAUDE.md protocols, Obsidian |
