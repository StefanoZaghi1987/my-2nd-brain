# Vault Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix five bugs in the fetch pipeline and linter, add three new linter checks, introduce the `/ingest` command, make the session lifecycle explicit in CLAUDE.md, and add a minimal Obsidian skeleton — all guided by the spec at `features/specs/2026-05-28-vault-hardening-design.md`.

**Architecture:** Two independent waves. Wave 1 is Python code with pytest coverage — fetch and linter changes are independent and can be parallelised. Wave 2 is prose and configuration — reviewable in one reading pass, no tests.

**Tech Stack:** Python 3.10+, pytest, requests-mock (already installed). Bash for init-vault.sh. Markdown for all command and skill files.

**Spec:** `features/specs/2026-05-28-vault-hardening-design.md`

**Working directory:** `D:\my-2nd-brain` — all paths are relative to this directory.

**Comment rule:** Write only comments that explain a non-obvious invariant or constraint. Never write comments that describe what a change does or why it was made.

**Setup (once):**
```bash
pip install pytest requests-mock
```

---

## Wave 1 — Code + Tests

*Tasks 1–7 are independent. Tasks 2–4 all modify `fetch_inbox.py`; do them sequentially. Tasks 5–7 all modify `lint.py`; do them sequentially. Tasks 1 can run in parallel with either group.*

---

### Task 1 — Add `reflect_reminder_days` config key

**Files:**
- Modify: `vault.config.yml`
- Modify: `skills/shared/vault_state.py`
- Modify: `tests/test_vault_state.py`

- [ ] **Step 1: Add a failing assertion to the existing config test**

Open `tests/test_vault_state.py`. In `TestLoadConfig.test_returns_all_default_sections_when_absent`, add one line at the end of the method:

```python
assert config["lint"]["reflect_reminder_days"] == 14
```

The full method after edit:

```python
def test_returns_all_default_sections_when_absent(self, tmp_path):
    config = load_config(tmp_path)
    assert config["inbox"]["processed_section"] == "## Processed"
    assert config["lint"]["stale_source_days"] == 180
    assert config["fetch"]["html_timeout_seconds"] == 20
    assert isinstance(config["fetch"]["walled_domains"], list)
    assert "x.com" in config["fetch"]["walled_domains"]
    assert config["lint"]["reflect_reminder_days"] == 14
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
pytest tests/test_vault_state.py::TestLoadConfig::test_returns_all_default_sections_when_absent -v
```

Expected: `FAILED` — `KeyError: 'reflect_reminder_days'`

- [ ] **Step 3: Add the default to `vault_state.py`**

In `skills/shared/vault_state.py`, find the `_DEFAULTS` dict. In the `"lint"` sub-dict, add the new key after `"auto_trigger_after_days"`:

```python
"lint": {
    "stale_source_days": 180,
    "view_stale_days": 30,
    "auto_trigger_after_ingests": 5,
    "auto_trigger_after_days": 7,
    "reflect_reminder_days": 14,
},
```

- [ ] **Step 4: Run the test — verify it passes**

```bash
pytest tests/test_vault_state.py::TestLoadConfig::test_returns_all_default_sections_when_absent -v
```

Expected: `PASSED`

- [ ] **Step 5: Add the key to `vault.config.yml`**

In `vault.config.yml`, find the `lint:` section and add the new key with an inline comment explaining when the reminder fires:

```yaml
lint:
  stale_source_days: 180             # advisory after this many days without update
  view_stale_days: 30                # days a view can lag its based_on pages
  auto_trigger_after_ingests: 5      # run lint automatically after N ingests
  auto_trigger_after_days: 7         # run lint automatically after N days
  reflect_reminder_days: 14          # suggest /reflect after N days without one
```

- [ ] **Step 6: Run all vault_state tests — verify nothing broke**

```bash
pytest tests/test_vault_state.py -v
```

Expected: all `PASSED`

- [ ] **Step 7: Commit**

```bash
git add vault.config.yml skills/shared/vault_state.py tests/test_vault_state.py
git commit -m "add reflect_reminder_days config key with default of 14 days"
```

---

### Task 2 — Fix `update_inbox` sub-bullet orphaning

**Files:**
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`
- Modify: `tests/test_fetch_inbox.py`

- [ ] **Step 1: Write three failing tests**

Add a new class to the end of `tests/test_fetch_inbox.py`:

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
            "  - note: important section\n"
        )
        results = [FetchResult(
            url="https://paywall.com/article", ok=False, kind="failed",
            reason="extraction empty — try playwright",
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "- [ ] https://paywall.com/article ⚠" in new_text
        assert "tags: ai" in new_text
        assert "note: important section" in new_text

    def test_unprocessed_url_keeps_sub_bullets(self):
        inbox = (
            "## To process\n"
            "- [ ] https://example.com/other\n"
            "  - tags: other\n"
        )
        new_text = update_inbox(Path("dummy"), inbox, [],
                                processed_section="## Processed")
        assert "- [ ] https://example.com/other" in new_text
        assert "tags: other" in new_text
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_fetch_inbox.py::TestUpdateInboxSubBullets -v
```

Expected: `test_successful_url_drops_sub_bullets` FAILS (sub-bullets still present), others may pass.

- [ ] **Step 3: Replace `update_inbox` in `fetch_inbox.py`**

Find `update_inbox` (starts around line 323) and replace the entire function body with the index-based implementation. The new function has the same signature:

```python
def update_inbox(
    inbox_path: Path,
    inbox_text: str,
    results: list[FetchResult],
    processed_section: str = "## Processed",
) -> str:
    """
    Rewrite inbox.md:
    - successful URLs are moved under the processed_section header
    - failed URLs stay unchecked with a ⚠ reason appended inline
    """
    lines = inbox_text.splitlines()
    today = date.today().isoformat()

    result_by_url = {r.url: r for r in results}
    new_processed_lines: list[str] = []
    out_lines: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        match = UNCHECKED_PATTERN.match(line)
        if not match:
            out_lines.append(line)
            i += 1
            continue

        url = match.group(1).strip()

        # Determine the span of indented sub-bullets that follow this URL line
        j = i + 1
        while j < len(lines) and (
            lines[j].startswith(" ") or lines[j].startswith("\t")
        ):
            j += 1

        if url not in result_by_url:
            # Not in this batch — preserve URL and sub-bullets unchanged
            out_lines.extend(lines[i:j])
            i = j
            continue

        result = result_by_url[url]
        if result.ok:
            rel = result.out_path
            new_processed_lines.append(
                f"- [x] {url} → `{rel}` ({today})"
            )
            # Sub-bullets have been written to raw frontmatter; drop them here
        else:
            out_lines.append(f"- [ ] {url} ⚠ {result.reason}")
            # Keep sub-bullets under the failure line for retry context
            out_lines.extend(lines[i + 1:j])

        i = j

    final_lines = list(out_lines)
    if new_processed_lines:
        if not any(l.strip() == processed_section for l in final_lines):
            if final_lines and final_lines[-1].strip():
                final_lines.append("")
            final_lines.append(processed_section)
            final_lines.append("")
        final_lines.extend(new_processed_lines)

    return "\n".join(final_lines) + ("\n" if inbox_text.endswith("\n") else "")
```

- [ ] **Step 4: Run all fetch_inbox tests — verify they pass**

```bash
pytest tests/test_fetch_inbox.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
git commit -m "update_inbox: drop sub-bullets on success, keep on failure"
```

---

### Task 3 — Enforce `pdf_enabled` config key

**Files:**
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`
- Modify: `tests/test_fetch_inbox.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_fetch_inbox.py`:

```python
class TestPdfEnabled:
    def test_pdf_url_skipped_when_disabled(self, tmp_path, requests_mock):
        from fetch_inbox import process_vault
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  pdf_enabled: false\n"
        )
        (tmp_path / "inbox.md").write_text(
            "- [ ] https://arxiv.org/pdf/2405.12345.pdf\n"
        )
        (tmp_path / "raw" / "papers").mkdir(parents=True)
        (tmp_path / "raw" / "web").mkdir(parents=True)
        # Safety net: if fetch_pdf is incorrectly called, this 403 makes it fail loudly
        requests_mock.get(
            "https://arxiv.org/pdf/2405.12345.pdf",
            status_code=403,
        )
        process_vault(tmp_path)
        inbox_text = (tmp_path / "inbox.md").read_text()
        assert "⚠" in inbox_text
        assert "pdf_enabled" in inbox_text
        assert not any(
            entry.is_file()
            for entry in (tmp_path / "raw" / "papers").rglob("*")
        )
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
pytest tests/test_fetch_inbox.py::TestPdfEnabled -v
```

Expected: `FAILED` — the PDF is fetched despite `pdf_enabled: false` (or the 403 causes a different error).

- [ ] **Step 3: Add `pdf_enabled` check in `process_vault`**

In `skills/inbox-fetcher/scripts/fetch_inbox.py`, find `process_vault`. After the config loading block, extract `pdf_enabled`:

```python
def process_vault(vault: Path, dry_run: bool = False) -> int:
    cfg = load_config(vault)
    processed_section = cfg["inbox"]["processed_section"]
    html_timeout = cfg["fetch"]["html_timeout_seconds"]
    pdf_timeout = cfg["fetch"]["pdf_timeout_seconds"]
    max_pdf_mb = cfg["fetch"]["max_pdf_size_mb"]
    walled = frozenset(cfg["fetch"]["walled_domains"])
    pdf_enabled = cfg["fetch"]["pdf_enabled"]
```

Then find the routing block inside the loop and add the `pdf_enabled` guard:

```python
        if is_pdf_url(fetch_url):
            if not pdf_enabled:
                r = FetchResult(
                    url=fetch_url, ok=False, kind="failed",
                    reason="PDF fetch disabled (pdf_enabled: false in vault.config.yml)",
                )
            else:
                r = fetch_pdf(fetch_url, papers_dir, slug_override=slug_override,
                              pdf_timeout=pdf_timeout, max_pdf_mb=max_pdf_mb,
                              tags=e.tags, note=e.note)
        elif is_walled(fetch_url, walled):
```

- [ ] **Step 4: Run all fetch_inbox tests — verify they pass**

```bash
pytest tests/test_fetch_inbox.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
git commit -m "honour pdf_enabled config key in fetch pipeline"
```

---

### Task 4 — Add Content-Type header detection for PDF routing

**Files:**
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`
- Modify: `tests/test_fetch_inbox.py`

- [ ] **Step 1: Write two failing tests**

Add to `tests/test_fetch_inbox.py`:

```python
class TestGetContentType:
    def test_returns_content_type_on_success(self, requests_mock):
        from fetch_inbox import get_content_type
        requests_mock.head(
            "https://example.com/doc",
            headers={"Content-Type": "application/pdf"},
        )
        assert get_content_type("https://example.com/doc") == "application/pdf"

    def test_returns_empty_string_on_connection_error(self, requests_mock):
        from fetch_inbox import get_content_type
        requests_mock.head(
            "https://example.com/broken",
            exc=ConnectionError("refused"),
        )
        assert get_content_type("https://example.com/broken") == ""


class TestContentTypeRouting:
    def test_pdf_without_suffix_routed_by_content_type(self, tmp_path, requests_mock):
        from fetch_inbox import process_vault
        (tmp_path / "inbox.md").write_text(
            "- [ ] https://example.com/download?id=42\n"
        )
        (tmp_path / "raw" / "papers").mkdir(parents=True)
        (tmp_path / "raw" / "web").mkdir(parents=True)
        requests_mock.head(
            "https://example.com/download?id=42",
            headers={"Content-Type": "application/pdf; charset=binary"},
        )
        requests_mock.get(
            "https://example.com/download?id=42",
            content=b"%PDF-1.4 fake",
        )
        process_vault(tmp_path)
        inbox_text = (tmp_path / "inbox.md").read_text()
        assert "[x]" in inbox_text
        papers = list((tmp_path / "raw" / "papers").iterdir())
        assert len(papers) == 1
        assert (papers[0] / "paper.pdf").exists()
        assert (papers[0] / "index.md").exists()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_fetch_inbox.py::TestGetContentType tests/test_fetch_inbox.py::TestContentTypeRouting -v
```

Expected: `ImportError: cannot import name 'get_content_type'`

- [ ] **Step 3: Add `get_content_type` function to `fetch_inbox.py`**

Add immediately after the `yaml_escape` function (before the "Inbox rewriting" section comment):

```python
def get_content_type(url: str, timeout: int = 10) -> str:
    """Probe a URL with a HEAD request; return the Content-Type value or empty string."""
    try:
        r = requests.head(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        return r.headers.get("Content-Type", "")
    except Exception:
        return ""
```

- [ ] **Step 4: Add the content-type branch to `process_vault` routing**

In `process_vault`, find the routing block modified in Task 3. Add the content-type branch between the walled check and the `fetch_html` fallback:

```python
        if is_pdf_url(fetch_url):
            if not pdf_enabled:
                r = FetchResult(
                    url=fetch_url, ok=False, kind="failed",
                    reason="PDF fetch disabled (pdf_enabled: false in vault.config.yml)",
                )
            else:
                r = fetch_pdf(fetch_url, papers_dir, slug_override=slug_override,
                              pdf_timeout=pdf_timeout, max_pdf_mb=max_pdf_mb,
                              tags=e.tags, note=e.note)
        elif is_walled(fetch_url, walled):
            host = urlparse(fetch_url).netloc.lower()
            r = FetchResult(
                url=fetch_url, ok=False, kind="failed",
                reason=f"walled domain ({host}) — {PLAYWRIGHT_HINT}",
            )
        elif "application/pdf" in get_content_type(fetch_url):
            if not pdf_enabled:
                r = FetchResult(
                    url=fetch_url, ok=False, kind="failed",
                    reason="PDF fetch disabled (pdf_enabled: false in vault.config.yml)",
                )
            else:
                r = fetch_pdf(fetch_url, papers_dir, slug_override=slug_override,
                              pdf_timeout=pdf_timeout, max_pdf_mb=max_pdf_mb,
                              tags=e.tags, note=e.note)
        else:
            r = fetch_html(fetch_url, web_dir, html_timeout=html_timeout,
                           tags=e.tags, note=e.note)
```

- [ ] **Step 5: Run all fetch_inbox tests — verify they pass**

```bash
pytest tests/test_fetch_inbox.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
git commit -m "route PDF responses without .pdf suffix via Content-Type header"
```

---

### Task 5 — Remove dead `ORPHAN_EXCEPTIONS` entries

**Files:**
- Modify: `skills/vault-linter/scripts/lint.py`

- [ ] **Step 1: Update the constant**

In `skills/vault-linter/scripts/lint.py`, find the `ORPHAN_EXCEPTIONS` set near the top of the file and replace it:

```python
ORPHAN_EXCEPTIONS = {
    "wiki/hot.md",
    "wiki/compass.md",
    "wiki/index.md",
    "wiki/log.md",
}
```

The two removed entries (`"index.md"` and `"log.md"`) never matched anything because `load_wiki()` always produces paths with the `wiki/` prefix.

- [ ] **Step 2: Run all lint tests — verify nothing broke**

```bash
pytest tests/test_lint.py -v
```

Expected: all `PASSED`

- [ ] **Step 3: Commit**

```bash
git add skills/vault-linter/scripts/lint.py
git commit -m "remove unreachable entries from ORPHAN_EXCEPTIONS"
```

---

### Task 6 — Add `check_conversations` linter function

**Files:**
- Modify: `skills/vault-linter/scripts/lint.py`
- Modify: `tests/test_lint.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_lint.py`:

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

    def test_advisory_for_missing_type_field(self, tmp_path):
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

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_lint.py::TestCheckConversations -v
```

Expected: `ImportError: cannot import name 'check_conversations'`

- [ ] **Step 3: Add `check_conversations` to `lint.py`**

Add the function after `check_missing_cross_references` (before the Report section):

```python
def check_conversations(vault: Path) -> list[Finding]:
    """Check that each file in conversations/ declares type: conversation."""
    findings = []
    conv_dir = vault / "conversations"
    if not conv_dir.is_dir():
        return findings

    for md_file in sorted(conv_dir.glob("*.md")):
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

- [ ] **Step 4: Register in `run_lint`**

In `run_lint`, find `all_checks` and add `check_conversations` at the end:

```python
all_checks = [
    ("dead_links", check_dead_links),
    ("based_on_dead_links", check_based_on_links),
    ("orphans", check_orphans),
    ("duplicates", lambda p: check_duplicates(p, duplicate_threshold)),
    ("missing_metadata", check_missing_metadata),
    ("inconsistent_naming", check_inconsistent_naming),
    ("stale_sources", lambda p: check_stale_sources(p, stale_source_days)),
    ("gaps", check_gaps),
    ("view_staleness", lambda p: check_view_staleness(p, view_stale_days)),
    ("missing_cross_references", check_missing_cross_references),
    ("pdf_index", check_pdf_index),
    ("conversations", check_conversations),
]
```

Then update the dispatcher to include `"conversations"` in the vault-only branch:

```python
        if name in ("dead_links", "orphans", "based_on_dead_links"):
            out = fn(pages, vault)
        elif name in ("pdf_index", "conversations"):
            out = fn(vault)
        else:
            out = fn(pages)
```

- [ ] **Step 5: Run all lint tests — verify they pass**

```bash
pytest tests/test_lint.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add skills/vault-linter/scripts/lint.py tests/test_lint.py
git commit -m "add check_conversations: advisory finding for missing type field"
```

---

### Task 7 — Add `check_index_sync` linter function

**Files:**
- Modify: `skills/vault-linter/scripts/lint.py`
- Modify: `tests/test_lint.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_lint.py`:

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

    def test_no_findings_when_source_listed_in_index(self, tmp_path):
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

    def test_advisory_when_source_absent_from_index(self, tmp_path):
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
        assert "agent-skills" in findings[0].file
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_lint.py::TestCheckIndexSync -v
```

Expected: `ImportError: cannot import name 'check_index_sync'`

- [ ] **Step 3: Add `check_index_sync` to `lint.py`**

Add after `check_conversations`:

```python
def check_index_sync(pages: dict[str, WikiPage], vault: Path) -> list[Finding]:
    """Verify that every wiki/sources/ entry is mentioned in wiki/index.md."""
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

- [ ] **Step 4: Register in `run_lint`**

In `all_checks`, add `check_index_sync` after `check_conversations`:

```python
    ("conversations", check_conversations),
    ("index_sync", check_index_sync),
```

Update the dispatcher to include `"index_sync"` in the two-argument branch:

```python
        if name in ("dead_links", "orphans", "based_on_dead_links", "index_sync"):
            out = fn(pages, vault)
        elif name in ("pdf_index", "conversations"):
            out = fn(vault)
        else:
            out = fn(pages)
```

- [ ] **Step 5: Run all tests — verify they pass**

```bash
pytest tests/ -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add skills/vault-linter/scripts/lint.py tests/test_lint.py
git commit -m "add check_index_sync: advisory finding when source omitted from index.md"
```

---

## Wave 2 — Documentation & Agent Protocols

*Tasks 8–14 are independent prose changes. Each can be committed individually.*

---

### Task 8 — Fix stale text in inbox-fetcher SKILL.md

**Files:**
- Modify: `skills/inbox-fetcher/SKILL.md`

- [ ] **Step 1: Update the sub-bullet description**

In `skills/inbox-fetcher/SKILL.md`, find the line in the `## Inbox format` section that reads:

```
- Indented sub-bullets (tags, notes) are preserved but not parsed — they're hints for the ingest step.
```

Replace it with:

```
- Indented sub-bullets (`- tags: tag1, tag2` and `- note: focus on X`) are parsed by the script and written into the raw source's `index.md` frontmatter. The ingest step reads them from there via tag/note propagation.
```

- [ ] **Step 2: Commit**

```bash
git add skills/inbox-fetcher/SKILL.md
git commit -m "correct sub-bullet description in inbox-fetcher SKILL.md"
```

---

### Task 9 — Fix `gaps` severity in vault-linter SKILL.md

**Files:**
- Modify: `skills/vault-linter/SKILL.md`

- [ ] **Step 1: Update the severity section**

In `skills/vault-linter/SKILL.md`, find the `## Output` → `.lint/report.md` subsection. Replace:

```
- **Important** — orphans, gaps.
- **Advisory** — duplicates, stale, naming, view staleness.
```

With:

```
- **Important** — orphans.
- **Advisory** — duplicates, stale, naming, view staleness, gaps, missing cross-references.
```

- [ ] **Step 2: Commit**

```bash
git add skills/vault-linter/SKILL.md
git commit -m "align gaps severity in SKILL.md with advisory level used in code"
```

---

### Task 10 — Add missing sixth invariant to README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the invariants section**

In `README.md`, find the `## Design principles` section. Change the heading from `Five invariants:` to `Six invariants:` and add the missing entry after invariant 5:

```markdown
## Design principles

Six invariants:

1. **Raw is immutable.** If the wiki is corrupted, it's recompilable
   from `raw/` alone.
2. **Every claim cites a source.** No orphan claims in the wiki.
3. **Paraphrase, don't copy.** Summaries are in the agent's words.
4. **You curate, the agent maintains.** No auto-fetching, no
   auto-structural changes, no views without your request.
5. **`shareable: true` views are frozen.** Anything else evolves.
6. **Touch ≤15 files per operation.** If more are needed, stop and
   ask — split the work across sessions.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "add missing sixth invariant to README design principles"
```

---

### Task 11 — Create `commands/ingest.md`

**Files:**
- Create: `commands/ingest.md`

- [ ] **Step 1: Write the file**

Create `commands/ingest.md` with this content:

```markdown
---
description: Compile raw sources into the wiki. Reads raw/web/ and raw/papers/ for
  sources that don't yet have a wiki/sources/<slug>.md entry, summarises each, links
  them into wiki/pages/, and updates wiki/index.md and wiki/log.md.
---

# /ingest — Compile raw sources into the wiki

## When to use

After running the inbox fetcher, or when new files have been added to `raw/` manually.
Also when asked to "ingest", "summarise the new sources", or "add this to the wiki".

## Discover targets

If no slug is given: scan `raw/web/` and `raw/papers/` for subdirectories that have an
`index.md` but no corresponding `wiki/sources/<slug>.md`. These are the uningested sources.

If a slug is given (`/ingest arxiv-2405-12345`): target that source only.

Confirm with the user before ingesting more than one source at a time:
> "Found N new sources: [list]. Ingest all?"

## Protocol

### Web articles

Source: `raw/web/<slug>/index.md` (no `fetch_method` field, or `fetch_method: html`).

1. Read `index.md` — get `source_url`, `title`, `tags`, `note`.
2. Read the article body.
3. Write `wiki/sources/<slug>.md` with a summary in your own words.
4. Propagate `tags` into the source frontmatter.
   If `note` is present, address that topic explicitly in the summary — not just
   acknowledge it.

### PDFs

Source: `raw/papers/<slug>/index.md` with `fetch_method: pdf`.

1. Read `index.md` — get `source_url`, `title`, `tags`, `note`.
2. Read `paper.pdf` using the Read tool — pages 1–5. If the paper has more than
   10 pages, also read the last 2 pages.
3. Infer the title from the first visible heading; fall back to the slug.
4. Write `wiki/sources/<slug>.md` with the same schema as web sources,
   plus `fetch_method: pdf` in frontmatter.
5. Propagate `tags` and `note` as above.

## Guards

- **≤3 new pages before confirm.** If ingesting a source would require creating more
  than 3 new `wiki/pages/` entries for emerging concepts, stop and list the proposed
  pages. Ask: "Create all three?" before writing any.
- **≤15 files per operation (invariant #6).** If a single ingest would touch more
  than 15 files, split across sessions. Report the count and ask which sources to
  prioritise.

## Completion steps

After every ingest, regardless of how many sources:

1. Update `wiki/index.md` — add a line under `## Sources` for each new source.
2. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <slug>` for each source.
3. Report to the user: sources ingested, pages created or updated, any guards triggered.
```

- [ ] **Step 2: Add `ingest` to the `init-vault.sh` command loop**

In `init-vault.sh`, find:

```bash
for cmd in save view reflect forget lint promote refresh; do
```

Replace with:

```bash
for cmd in save view reflect forget lint promote refresh ingest; do
```

- [ ] **Step 3: Commit**

```bash
git add commands/ingest.md init-vault.sh
git commit -m "add /ingest command and register it in init-vault.sh"
```

---

### Task 12 — Add session-start section and sharpen invariant #6 in CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Insert the session-start section**

In `CLAUDE.md`, find the line `## Hot cache` and read to the end of that section (it ends just before `## Unattended mode`). Insert the new section between `## Hot cache` and `## Unattended mode`:

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

- [ ] **Step 2: Sharpen invariant #6**

In the `## Six invariants — never break these` section, find invariant #6. Replace:

```
6. **Update `index.md` and `log.md`** after any writing operation.
```

With:

```
6. **Update `wiki/index.md` and `wiki/log.md`** after any writing operation —
   add new source/page/view entries to `wiki/index.md`; append an operation line
   to `wiki/log.md`.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "add session-start protocol and clarify invariant 6 in CLAUDE.md"
```

---

### Task 13 — Update `commands/save.md` conversation template

**Files:**
- Modify: `commands/save.md`

- [ ] **Step 1: Add `type` and `promoted_to` to the template**

In `commands/save.md`, find the `## Template` section. Replace the frontmatter block inside the code fence:

```markdown
---
date: YYYY-MM-DD
tags: [tag1, tag2]
pages_read:
  - [[wiki/pages/x]]
pages_written:
  - [[wiki/pages/x]]
views_used:
  - [[wiki/views/timeline-y]]
---
```

With:

```markdown
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

- [ ] **Step 2: Commit**

```bash
git add commands/save.md
git commit -m "add type:conversation and promoted_to fields to /save template"
```

---

### Task 14 — Add Obsidian skeleton to `init-vault.sh`

**Files:**
- Modify: `init-vault.sh`

- [ ] **Step 1: Add `.obsidian` to the DIRS array**

In `init-vault.sh`, find the `DIRS=(` block. Add `.obsidian` as the last entry before the closing `)`:

```bash
DIRS=(
    "raw/papers"
    "raw/web"
    "wiki/pages"
    "wiki/sources"
    "wiki/views/assets"
    "conversations"
    ".lint"
    ".claude/skills/inbox-fetcher/scripts"
    ".claude/skills/vault-linter/scripts"
    ".claude/skills/view-builder/templates"
    ".claude/skills/shared"
    ".claude/commands"
    ".obsidian"
)
```

- [ ] **Step 2: Add `.obsidian/app.json` creation block**

After the `.gitignore` creation block (find the line `ok ".gitignore"`), add the Obsidian block. The full block to insert, matching the surrounding style:

```bash
# --- Obsidian config -------------------------------------------------------
info "Obsidian"
if [ ! -f "$VAULT_DIR/.obsidian/app.json" ]; then
    cat > "$VAULT_DIR/.obsidian/app.json" <<'EOF'
{
  "useMarkdownLinks": false,
  "newLinkFormat": "relative",
  "readableLineLength": true,
  "attachmentFolderPath": "wiki/views/assets"
}
EOF
    ok ".obsidian/app.json"
else
    skip ".obsidian/app.json (exists — keeping user config)"
fi
```

- [ ] **Step 3: Verify the script runs without errors**

```bash
bash init-vault.sh /tmp/test-vault-hardening
ls /tmp/test-vault-hardening/.obsidian/app.json
cat /tmp/test-vault-hardening/.obsidian/app.json
ls /tmp/test-vault-hardening/.claude/commands/ingest.md
rm -rf /tmp/test-vault-hardening
```

Expected: `app.json` exists with `useMarkdownLinks: false`. `ingest.md` exists in commands.

- [ ] **Step 4: Commit**

```bash
git add init-vault.sh
git commit -m "add Obsidian skeleton to init-vault.sh bootstrap"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Implemented in |
|-----------------|----------------|
| §1.1 update_inbox sub-bullet fix + 3 tests | Task 2 |
| §1.2 pdf_enabled enforcement + test | Task 3 |
| §1.3 get_content_type + routing + tests | Task 4 |
| §1.4 ORPHAN_EXCEPTIONS dead entries | Task 5 |
| §1.5 check_conversations + tests | Task 6 |
| §1.6 check_index_sync + tests | Task 7 |
| §1.7 reflect_reminder_days in vault.config.yml + vault_state.py + test | Task 1 |
| §2.1 SKILL.md inbox-fetcher stale text | Task 8 |
| §2.2 SKILL.md vault-linter gaps severity | Task 9 |
| §2.3 README six invariants | Task 10 |
| §2.4 commands/ingest.md + init-vault.sh command loop | Task 11 |
| §2.5 CLAUDE.md session-start section | Task 12 |
| §2.6 CLAUDE.md invariant #6 sharpened | Task 12 |
| §2.7 commands/save.md type + promoted_to | Task 13 |
| §2.8 init-vault.sh Obsidian skeleton | Task 14 |

All 15 spec sections covered. No gaps.

**Placeholder scan:** No TBDs, TODOs, or "similar to above" shortcuts found. All code steps include full implementations.

**Type/signature consistency:**

- `update_inbox(inbox_path, inbox_text, results, processed_section)` — same signature in Task 2 implementation and all existing callers. ✓
- `get_content_type(url, timeout=10) -> str` — defined in Task 4 Step 3, used in Task 4 Step 4. ✓
- `process_vault` reads `pdf_enabled = cfg["fetch"]["pdf_enabled"]` in Task 3; same key used in Task 4 content-type branch. ✓
- `check_conversations(vault: Path) -> list[Finding]` — defined Task 6 Step 3, registered in Task 6 Step 4 under `("pdf_index", "conversations")` branch. ✓
- `check_index_sync(pages: dict[str, WikiPage], vault: Path) -> list[Finding]` — defined Task 7 Step 3, registered Task 7 Step 4 under `("dead_links", "orphans", "based_on_dead_links", "index_sync")` branch. ✓
- `_DEFAULTS["lint"]["reflect_reminder_days"]` added Task 1 Step 3; matching key in `vault.config.yml` Task 1 Step 5. ✓
