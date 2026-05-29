# Markdown Drop-Zone Ingestion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `raw/drop/` to accept `.md` files alongside PDFs so users can drop any Markdown file, run `/ingest`, and have it automatically adopted into `raw/local/<slug>/` and ingested into the wiki.

**Architecture:** A type-handler registry (`HANDLERS` dict) in `adopt_drop.py` dispatches `.pdf` and `.md` files to dedicated handler functions. `adopt_md()` extracts title and source URL from the file's content, writes a vault-standard `index.md` stub, then atomically renames the original file to `content.md`. The LLM's `/ingest` command gains a `local-md` protocol branch that reads `content.md` in full.

**Tech Stack:** Python 3.10+ stdlib only (`re`, `pathlib`, `datetime`). Test runner: `pytest`. No new dependencies.

---

## File Map

| File | Change |
|---|---|
| `skills/inbox-fetcher/scripts/adopt_drop.py` | Add `import re`, extraction helpers, `adopt_md()`, `HANDLERS` registry, refactor `process_drop_zone()` |
| `tests/test_adopt_drop.py` | Add `TestExtractHelpers`, `TestAdoptMd`, update `TestProcessDropZone` |
| `skills/vault-linter/scripts/lint.py` | Update `check_drop_zone()` to detect `.md` files |
| `tests/test_lint.py` | Add `.md` detection test to `TestCheckDropZone` |
| `commands/ingest.md` | Update pre-flight step 2 wording; add `local-md` protocol branch |
| `CLAUDE.md` | Update vault structure diagram; add `local-md` source type branch |
| `skills/inbox-fetcher/SKILL.md` | Document `adopt_md()` in drop zone adoption section |
| `skills/vault-linter/SKILL.md` | Update `drop_zone_not_empty` check description |

---

## Task 1: Extraction helper functions

**Files:**
- Modify: `skills/inbox-fetcher/scripts/adopt_drop.py`
- Modify: `tests/test_adopt_drop.py`

- [ ] **Step 1.1: Write failing tests for `extract_title_from_md`**

Add a new class to `tests/test_adopt_drop.py`:

```python
class TestExtractTitleFromMd:
    def test_returns_frontmatter_title(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text('---\ntitle: "My Obsidian Note"\n---\n# Different Heading\nsome body')
        assert extract_title_from_md(f) == "My Obsidian Note"

    def test_frontmatter_title_without_quotes(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("---\ntitle: Plain Title\n---\nsome body")
        assert extract_title_from_md(f) == "Plain Title"

    def test_falls_back_to_h1_when_no_frontmatter_title(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("---\nauthor: Alice\n---\n# My Heading\nsome body")
        assert extract_title_from_md(f) == "My Heading"

    def test_falls_back_to_h1_when_no_frontmatter(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("# My Heading\nsome body")
        assert extract_title_from_md(f) == "My Heading"

    def test_returns_none_when_nothing_found(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("just some prose with no heading")
        assert extract_title_from_md(f) is None

    def test_handles_empty_frontmatter(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("---\n---\n# Heading After Empty\n")
        assert extract_title_from_md(f) == "Heading After Empty"

    def test_handles_malformed_frontmatter_no_closing(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("---\ntitle: orphan\n# Heading\n")
        # No closing ---, frontmatter regex won't match; falls to H1
        assert extract_title_from_md(f) == "Heading"
```

- [ ] **Step 1.2: Run tests to confirm they fail**

```bash
cd D:\my-2nd-brain
python -m pytest tests/test_adopt_drop.py::TestExtractTitleFromMd -v
```

Expected: `ImportError: cannot import name 'extract_title_from_md' from 'adopt_drop'`

- [ ] **Step 1.3: Write failing tests for `extract_source_url_from_md`**

Add another class to `tests/test_adopt_drop.py`:

```python
class TestExtractSourceUrlFromMd:
    def test_reads_source_url_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "clip.md"
        f.write_text("---\nsource_url: https://example.com/article\n---\nbody")
        assert extract_source_url_from_md(f) == "https://example.com/article"

    def test_reads_url_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "clip.md"
        f.write_text("---\nurl: https://example.com\n---\nbody")
        assert extract_source_url_from_md(f) == "https://example.com"

    def test_reads_link_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "clip.md"
        f.write_text("---\nlink: https://example.com\n---\nbody")
        assert extract_source_url_from_md(f) == "https://example.com"

    def test_reads_source_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "clip.md"
        f.write_text("---\nsource: https://example.com\n---\nbody")
        assert extract_source_url_from_md(f) == "https://example.com"

    def test_returns_none_when_no_known_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "note.md"
        f.write_text("---\ntitle: My Note\nauthor: Alice\n---\nbody")
        assert extract_source_url_from_md(f) is None

    def test_returns_none_when_no_frontmatter(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "note.md"
        f.write_text("# Just a heading\nno frontmatter here")
        assert extract_source_url_from_md(f) is None

    def test_handles_empty_frontmatter(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "note.md"
        f.write_text("---\n---\nbody")
        assert extract_source_url_from_md(f) is None
```

- [ ] **Step 1.4: Implement both helpers in `adopt_drop.py`**

Add `import re` at the top of `skills/inbox-fetcher/scripts/adopt_drop.py` (after the existing stdlib imports):

```python
import re
```

Then add both functions after `title_from_slug()` (before `AdoptResult`):

```python
def extract_title_from_md(path: Path) -> str | None:
    """Cascade: frontmatter title: → first # H1 → None."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if line.startswith("title:"):
                _, _, value = line.partition(":")
                value = value.strip().strip("\"'")
                if value:
                    return value

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()

    return None


def extract_source_url_from_md(path: Path) -> str | None:
    """Check frontmatter for source_url, url, link, source keys."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        return None

    fm_block = fm_match.group(1)
    for key in ("source_url", "url", "link", "source"):
        for line in fm_block.splitlines():
            if line.startswith(f"{key}:"):
                _, _, value = line.partition(":")
                value = value.strip().strip("\"'")
                if value:
                    return value
    return None
```

- [ ] **Step 1.5: Run all extraction tests**

```bash
cd D:\my-2nd-brain
python -m pytest tests/test_adopt_drop.py::TestExtractTitleFromMd tests/test_adopt_drop.py::TestExtractSourceUrlFromMd -v
```

Expected: all 14 tests PASS

- [ ] **Step 1.6: Run full test suite to confirm no regressions**

```bash
python -m pytest tests/test_adopt_drop.py -v
```

Expected: all existing tests still PASS

- [ ] **Step 1.7: Commit**

```bash
git add skills/inbox-fetcher/scripts/adopt_drop.py tests/test_adopt_drop.py
git commit -m "feat(ingest): add extract_title_from_md and extract_source_url_from_md helpers"
```

---

## Task 2: `adopt_md()` handler function

**Files:**
- Modify: `skills/inbox-fetcher/scripts/adopt_drop.py`
- Modify: `tests/test_adopt_drop.py`

- [ ] **Step 2.1: Write failing tests for `adopt_md`**

Add to `tests/test_adopt_drop.py`:

```python
class TestAdoptMd:
    def _make_drop(self, tmp_path):
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)
        return drop, local

    def test_moves_file_and_creates_index(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        md_file = drop / "my-note.md"
        md_file.write_text("# My Note\nsome content")

        result = adopt_md(md_file, local)

        assert result.ok
        assert result.slug == "my-note"
        assert not md_file.exists()
        assert (local / "my-note" / "content.md").exists()
        assert (local / "my-note" / "content.md").read_text() == "# My Note\nsome content"
        assert (local / "my-note" / "index.md").exists()

    def test_index_has_required_frontmatter_fields(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        (drop / "my-note.md").write_text("# My Note\ncontent")

        adopt_md(drop / "my-note.md", local)

        index = (local / "my-note" / "index.md").read_text()
        assert "fetch_method: local-md" in index
        assert "title:" in index
        assert "fetched:" in index
        assert "tags: []" in index
        assert "Content: [[content.md]]" in index

    def test_title_extracted_from_h1(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        (drop / "my-note.md").write_text("# Extracted Title\ncontent")

        adopt_md(drop / "my-note.md", local)

        index = (local / "my-note" / "index.md").read_text()
        assert 'title: "Extracted Title"' in index

    def test_title_extracted_from_frontmatter(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        (drop / "my-note.md").write_text('---\ntitle: "FM Title"\n---\n# H1 Title\ncontent')

        adopt_md(drop / "my-note.md", local)

        index = (local / "my-note" / "index.md").read_text()
        assert 'title: "FM Title"' in index

    def test_title_falls_back_to_slug_when_no_title(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        (drop / "my-note.md").write_text("just prose, no heading")

        adopt_md(drop / "my-note.md", local)

        index = (local / "my-note" / "index.md").read_text()
        assert 'title: "My Note"' in index

    def test_source_url_written_when_found(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        (drop / "web-clip.md").write_text(
            "---\nurl: https://example.com/article\n---\n# Article\ncontent"
        )

        adopt_md(drop / "web-clip.md", local)

        index = (local / "web-clip" / "index.md").read_text()
        assert "source_url: https://example.com/article" in index

    def test_source_url_omitted_when_not_found(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        (drop / "personal-note.md").write_text("# Personal Note\nno url here")

        adopt_md(drop / "personal-note.md", local)

        index = (local / "personal-note" / "index.md").read_text()
        assert "source_url" not in index

    def test_skips_on_slug_collision(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        (local / "my-note").mkdir(parents=True)
        md_file = drop / "my-note.md"
        md_file.write_text("content")

        result = adopt_md(md_file, local)

        assert not result.ok
        assert "already exists" in result.reason
        assert md_file.exists()

    def test_dry_run_creates_nothing(self, tmp_path):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        md_file = drop / "my-note.md"
        md_file.write_text("# My Note\ncontent")

        result = adopt_md(md_file, local, dry_run=True)

        assert result.ok
        assert md_file.exists()
        assert not (local / "my-note").exists()

    def test_rollback_on_index_write_failure(self, tmp_path, monkeypatch):
        from adopt_drop import adopt_md
        drop, local = self._make_drop(tmp_path)
        md_file = drop / "my-note.md"
        md_file.write_text("# My Note\ncontent")

        original_write_text = Path.write_text

        def failing_write(self, *args, **kwargs):
            if self.name == "index.md":
                raise OSError("simulated disk full")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", failing_write)

        with pytest.raises(OSError, match="simulated disk full"):
            adopt_md(md_file, local)

        assert md_file.exists()
        assert not (local / "my-note").exists()
```

- [ ] **Step 2.2: Run tests to confirm they fail**

```bash
cd D:\my-2nd-brain
python -m pytest tests/test_adopt_drop.py::TestAdoptMd -v
```

Expected: `ImportError: cannot import name 'adopt_md' from 'adopt_md'`

- [ ] **Step 2.3: Implement `adopt_md()` in `adopt_drop.py`**

Add after the `adopt_pdf()` function (before `process_drop_zone`):

```python
def adopt_md(md_path: Path, local_dir: Path, dry_run: bool = False) -> AdoptResult:
    """Adopt a single Markdown file from the drop zone into raw/local/<slug>/."""
    slug = slug_from_filename(md_path.name)
    if not slug:
        return AdoptResult(filename=md_path.name, slug="", ok=False,
                           reason="could not derive a slug from filename")

    out_dir = local_dir / slug
    if out_dir.is_dir():
        return AdoptResult(filename=md_path.name, slug=slug, ok=False,
                           reason=f"raw/local/{slug}/ already exists - skipped")

    if dry_run:
        return AdoptResult(filename=md_path.name, slug=slug, ok=True)

    out_dir.mkdir(parents=True, exist_ok=True)

    title = extract_title_from_md(md_path) or title_from_slug(slug)
    source_url = extract_source_url_from_md(md_path)

    index_lines = [
        "---",
        "fetch_method: local-md",
        f'title: "{title}"',
        f"fetched: {date.today().isoformat()}",
    ]
    if source_url:
        index_lines.append(f"source_url: {source_url}")
    index_lines += ["tags: []", "---", "", "Content: [[content.md]]", ""]

    index_path = out_dir / "index.md"
    try:
        index_path.write_text("\n".join(index_lines), encoding="utf-8")
    except Exception:
        index_path.unlink(missing_ok=True)
        out_dir.rmdir()
        raise

    try:
        md_path.rename(out_dir / "content.md")
    except Exception:
        index_path.unlink(missing_ok=True)
        out_dir.rmdir()
        raise

    return AdoptResult(filename=md_path.name, slug=slug, ok=True)
```

- [ ] **Step 2.4: Run `TestAdoptMd` tests**

```bash
cd D:\my-2nd-brain
python -m pytest tests/test_adopt_drop.py::TestAdoptMd -v
```

Expected: all 10 tests PASS

- [ ] **Step 2.5: Run full test suite**

```bash
python -m pytest tests/test_adopt_drop.py -v
```

Expected: all tests PASS

- [ ] **Step 2.6: Commit**

```bash
git add skills/inbox-fetcher/scripts/adopt_drop.py tests/test_adopt_drop.py
git commit -m "feat(ingest): add adopt_md() handler for Markdown drop-zone adoption"
```

---

## Task 3: Type-handler registry and orchestrator refactor

**Files:**
- Modify: `skills/inbox-fetcher/scripts/adopt_drop.py`
- Modify: `tests/test_adopt_drop.py`

- [ ] **Step 3.1: Write failing tests for the new orchestrator behavior**

Add to `tests/test_adopt_drop.py` — update the existing `TestProcessDropZone` class with new tests at the end:

```python
    def test_adopts_md_file(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "my-note.md").write_text("# My Note\ncontent")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 0
        assert (tmp_path / "raw" / "local" / "my-note" / "content.md").exists()
        assert (tmp_path / "raw" / "local" / "my-note" / "index.md").exists()

    def test_adopts_mixed_pdf_and_md(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper.pdf").write_bytes(b"%PDF")
        (drop / "note.md").write_text("# Note\ncontent")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 0
        assert (tmp_path / "raw" / "local" / "paper" / "paper.pdf").exists()
        assert (tmp_path / "raw" / "local" / "note" / "content.md").exists()

    def test_unsupported_types_ignored_md_still_adopted(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "doc.docx").write_bytes(b"fake docx")
        (drop / "note.md").write_text("# Note\ncontent")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 0
        assert (drop / "doc.docx").exists()  # docx not moved
        assert (tmp_path / "raw" / "local" / "note" / "content.md").exists()
```

- [ ] **Step 3.2: Run new tests to confirm they fail**

```bash
cd D:\my-2nd-brain
python -m pytest tests/test_adopt_drop.py::TestProcessDropZone::test_adopts_md_file tests/test_adopt_drop.py::TestProcessDropZone::test_adopts_mixed_pdf_and_md tests/test_adopt_drop.py::TestProcessDropZone::test_unsupported_types_ignored_md_still_adopted -v
```

Expected: FAIL (process_drop_zone ignores .md files today)

- [ ] **Step 3.3: Add `HANDLERS` registry and refactor `process_drop_zone()`**

First, add the import at the top of `adopt_drop.py` (after the existing imports, before the `MISSING_DEPS` block):

```python
from collections.abc import Callable
```

After the `adopt_md` function (before `process_drop_zone`), add the registry. Note: this must come AFTER both `adopt_pdf` and `adopt_md` are defined, since the dict references them:

```python
HANDLERS: dict[str, Callable[[Path, Path, bool], AdoptResult]] = {
    ".pdf": adopt_pdf,
    ".md":  adopt_md,
}
```

Replace the body of `process_drop_zone()` from the `all_files` line through the `results` loop with:

```python
    all_files = [p for p in drop_dir.iterdir() if p.is_file()]
    supported   = [f for f in all_files if f.suffix.lower() in HANDLERS]
    unsupported = [f for f in all_files if f.suffix.lower() not in HANDLERS]

    for f in unsupported:
        print(f"  [!] ignored (unsupported type): {f.name}")

    if not supported:
        print("Drop zone empty. Nothing to adopt.")
        return 0

    type_labels = {".pdf": "PDF", ".md": "Markdown"}
    counts: dict[str, int] = {}
    for f in supported:
        ext = f.suffix.lower()
        counts[ext] = counts.get(ext, 0) + 1
    parts = [f"{counts[e]} {type_labels.get(e, e[1:].upper())}(s)" for e in sorted(counts)]
    print(f"Found {' and '.join(parts)} in drop zone.")

    if dry_run:
        for f in supported:
            print(f"  would adopt: {f.name} -> raw/local/{slug_from_filename(f.name)}/")
        return 0

    results: list[AdoptResult] = []
    for f in supported:
        handler = HANDLERS[f.suffix.lower()]
        r = handler(f, local_dir, dry_run=dry_run)
        results.append(r)
        if r.ok:
            print(f"  [ok] adopted  raw/local/{r.slug}/")
        else:
            print(f"  [!] {r.reason}")
```

- [ ] **Step 3.4: Run full `TestProcessDropZone` suite**

```bash
cd D:\my-2nd-brain
python -m pytest tests/test_adopt_drop.py::TestProcessDropZone -v
```

Expected: all tests PASS, including the pre-existing ones (`test_ignores_non_pdf_files` now passes because `.docx` is still in `unsupported`)

- [ ] **Step 3.5: Run entire test suite**

```bash
python -m pytest tests/test_adopt_drop.py -v
```

Expected: all tests PASS

- [ ] **Step 3.6: Commit**

```bash
git add skills/inbox-fetcher/scripts/adopt_drop.py tests/test_adopt_drop.py
git commit -m "feat(ingest): type-handler registry in adopt_drop.py, adopt .md and .pdf via HANDLERS"
```

---

## Task 4: Update `commands/ingest.md`

**Files:**
- Modify: `commands/ingest.md`

No code — this is an LLM instruction file. Read it before editing.

- [ ] **Step 4.1: Update pre-flight step 2**

In `commands/ingest.md`, find the pre-flight block. Change step 2 from:

```
2. Scan for `*.pdf` files in the drop zone.
```

To:

```
2. Scan for files with supported types (`.pdf`, `.md`) in the drop zone.
```

- [ ] **Step 4.2: Add `local-md` protocol branch**

In the `## Protocol` section, after the `### PDFs` subsection (which ends around line 94), add:

```markdown
### Local Markdown files

Source: `raw/local/<slug>/index.md` with `fetch_method: local-md`.

1. Read `index.md` — get `title`, `source_url` (if present), `tags`, `note`.
2. Read `content.md` in full (plain text; no page limit).
3. Infer real title from content if better than index.md title
   (first H1 heading takes precedence over the filename-derived title).
4. Write `wiki/sources/<slug>.md`:
   - Include `source_url` only if present in `index.md`.
   - `source_path: raw/local/<slug>/`
   - `fetch_method: local-md`
5. Propagate `tags` and `note` as with other source types.
```

- [ ] **Step 4.3: Commit**

```bash
git add commands/ingest.md
git commit -m "feat(ingest): add local-md protocol branch to /ingest command"
```

---

## Task 5: Update `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

No code — this is the vault's primary LLM instruction file. Read the INGEST section before editing.

- [ ] **Step 5.1: Update vault structure diagram**

Find the vault structure diagram under `## Vault structure`. Update the `raw/` section. Change:

```
  local/<slug>/       PDFs copy-pasted by the user
```

To:

```
  local/<slug>/       PDFs or Markdown files copy-pasted by the user
```

And:

```
  drop/               Drop zone — paste PDFs here; emptied by /ingest
```

To:

```
  drop/               Drop zone — paste files here; emptied by /ingest
```

- [ ] **Step 5.2: Add `local-md` source type branch**

In the `### INGEST — source type branches` section, after the `**Local PDFs**` branch, add:

```markdown
**Local Markdown files** (`raw/local/<slug>/index.md` with `fetch_method: local-md`):
1. Read `index.md` — get `title`, `source_url` (if present), `tags`, `note`. There is no `source_url` if none was found at adoption time.
2. Read `content.md` in full (plain text; no page limit).
3. Infer real title from content if better than index.md title.
4. Write `wiki/sources/<slug>.md` — omit `source_url` field if not present.
   Use `source_path: raw/local/<slug>/` and `fetch_method: local-md` in frontmatter.
5. Carry `tags` and `note` as with other source types.
```

- [ ] **Step 5.3: Commit**

```bash
git add CLAUDE.md
git commit -m "feat(ingest): update CLAUDE.md vault structure and add local-md ingest branch"
```

---

## Task 6: Update `check_drop_zone` in `lint.py`

**Files:**
- Modify: `skills/vault-linter/scripts/lint.py`
- Modify: `tests/test_lint.py`

- [ ] **Step 6.1: Write failing test**

Read `tests/test_lint.py` first. Find the class that tests `check_drop_zone`. Add a new test to it:

```python
def test_detects_md_files_in_drop_zone(self, tmp_path):
    from lint import check_drop_zone
    (tmp_path / "vault.config.yml").write_text(
        "drop_zone:\n  enabled: true\n  path: raw/drop\n"
    )
    drop = tmp_path / "raw" / "drop"
    drop.mkdir(parents=True)
    (drop / "my-note.md").write_text("# My Note\ncontent")

    findings = check_drop_zone(tmp_path)

    assert len(findings) == 1
    assert findings[0].check == "drop_zone_not_empty"
    assert "Markdown" in findings[0].detail

def test_reports_mixed_types_in_drop_zone(self, tmp_path):
    from lint import check_drop_zone
    (tmp_path / "vault.config.yml").write_text(
        "drop_zone:\n  enabled: true\n  path: raw/drop\n"
    )
    drop = tmp_path / "raw" / "drop"
    drop.mkdir(parents=True)
    (drop / "paper.pdf").write_bytes(b"%PDF")
    (drop / "note.md").write_text("# Note\n")

    findings = check_drop_zone(tmp_path)

    assert len(findings) == 1
    assert "PDF" in findings[0].detail
    assert "Markdown" in findings[0].detail
```

- [ ] **Step 6.2: Run tests to confirm they fail**

```bash
cd D:\my-2nd-brain
python -m pytest tests/test_lint.py -k "drop_zone" -v
```

Expected: the two new tests FAIL (current code only checks .pdf)

- [ ] **Step 6.3: Update `check_drop_zone` in `lint.py`**

In `skills/vault-linter/scripts/lint.py`, add a constant just before `check_drop_zone` (around line 372):

```python
# Extensions mirroring adopt_drop.py HANDLERS keys
_DROP_ZONE_SUPPORTED = {".pdf", ".md"}
```

Replace the body of `check_drop_zone()` (keep the function signature and docstring):

```python
def check_drop_zone(vault: Path) -> list[Finding]:
    """Advisory check: supported files in the drop zone have not been adopted yet."""
    cfg = load_config(vault)
    if not cfg["drop_zone"]["enabled"]:
        return []
    drop_path = cfg["drop_zone"]["path"]
    drop_dir = vault / drop_path
    if not drop_dir.is_dir():
        return []

    type_labels = {".pdf": "PDF", ".md": "Markdown"}
    counts: dict[str, int] = {}
    for p in drop_dir.iterdir():
        if p.is_file() and p.suffix.lower() in _DROP_ZONE_SUPPORTED:
            ext = p.suffix.lower()
            counts[ext] = counts.get(ext, 0) + 1

    if not counts:
        return []

    parts = [f"{counts[e]} {type_labels.get(e, e[1:].upper())}(s)" for e in sorted(counts)]
    detail = f"Drop zone has {' and '.join(parts)} - run /ingest to adopt them."

    return [Finding(
        severity="advisory",
        check="drop_zone_not_empty",
        file=str(drop_dir.relative_to(vault)),
        detail=detail,
    )]
```

- [ ] **Step 6.4: Run drop zone tests**

```bash
cd D:\my-2nd-brain
python -m pytest tests/test_lint.py -k "drop_zone" -v
```

Expected: all drop zone tests PASS

- [ ] **Step 6.5: Run full lint test suite**

```bash
python -m pytest tests/test_lint.py -v
```

Expected: all tests PASS

- [ ] **Step 6.6: Commit**

```bash
git add skills/vault-linter/scripts/lint.py tests/test_lint.py
git commit -m "feat(ingest): extend check_drop_zone to detect .md files in drop zone"
```

---

## Task 7: Update SKILL.md documentation

**Files:**
- Modify: `skills/inbox-fetcher/SKILL.md`
- Modify: `skills/vault-linter/SKILL.md`

No tests — documentation only. Read both files in full before editing.

- [ ] **Step 7.1: Update `skills/inbox-fetcher/SKILL.md`**

Find the `## Drop zone adoption` section. Make these changes:

1. Update the section opening sentence from "Companion script for copy-pasted PDFs" to "Companion script for copy-pasted PDFs and Markdown files".

2. Update the "When to use" line: change "when `raw/drop/` ... contains `.pdf` files" to "when `raw/drop/` contains `.pdf` or `.md` files".

3. Update the "What it does per file" list — the current list covers PDF adoption steps. Add a sub-section after it:

```markdown
**For `.md` files** (`adopt_md()`):
1. Derives a slug from the filename stem via `slugify()`.
2. Checks for collision: if `raw/local/<slug>/` already exists, skips with a warning.
3. Creates `raw/local/<slug>/`.
4. Extracts title: checks frontmatter `title:` → first `# H1` heading → filename stem.
5. Extracts source URL: checks frontmatter keys `source_url`, `url`, `link`, `source` in order.
6. Writes a stub `index.md` with `fetch_method: local-md`, extracted title, and `source_url` if found.
7. Renames original file to `content.md` (atomic move; original preserved unchanged).
```

4. Replace the output contract example with a mixed-type example:

```markdown
**Output contract (live run, mixed types):**
```
Found 2 PDF(s) and 1 Markdown file(s) in drop zone.
  [ok] adopted  raw/local/attention-is-all-you-need/
  [ok] adopted  raw/local/lecun-path-to-autonomy/
  [ok] adopted  raw/local/my-obsidian-note/
Adopted 3, skipped 0.
```
```

- [ ] **Step 7.2: Update `skills/vault-linter/SKILL.md`**

Find the check table. Locate the row for `drop_zone_not_empty`. Update its description from "PDFs in the drop zone" (or similar) to "PDFs or Markdown files in the drop zone have not been adopted."

- [ ] **Step 7.3: Commit**

```bash
git add skills/inbox-fetcher/SKILL.md skills/vault-linter/SKILL.md
git commit -m "docs(ingest): update SKILL.md files to document Markdown drop-zone adoption"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Task |
|---|---|
| §5 Extraction helpers | Task 1 |
| §5 `adopt_md()` handler | Task 2 |
| §5 HANDLERS registry + orchestrator | Task 3 |
| §6 `/ingest` pre-flight wording | Task 4 |
| §6 `local-md` protocol branch | Task 4 |
| §7 CLAUDE.md structure diagram | Task 5 |
| §7 CLAUDE.md `local-md` branch | Task 5 |
| §8 `check_drop_zone` update | Task 6 |
| §9 SKILL.md documentation | Task 7 |

All spec sections covered. ✓

**Placeholder scan:** No TBD, TODO, or incomplete steps found. ✓

**Type consistency check:**
- `AdoptResult` used in Tasks 1–3: same dataclass throughout ✓
- `extract_title_from_md(path: Path) -> str | None` defined in Task 1, used in Task 2 ✓
- `extract_source_url_from_md(path: Path) -> str | None` defined in Task 1, used in Task 2 ✓
- `HANDLERS` defined in Task 3, referenced in `process_drop_zone` in Task 3 ✓
- `_DROP_ZONE_SUPPORTED` defined and used within `lint.py` in Task 6 ✓
