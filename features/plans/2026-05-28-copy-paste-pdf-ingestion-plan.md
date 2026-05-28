# Copy-Paste PDF Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow users to drop PDF files into `raw/drop/`, run `/ingest`, and have them automatically adopted into `raw/local/<slug>/` and ingested into the wiki.

**Architecture:** A new Python script (`adopt_drop.py`) handles the raw-layer adoption (scan drop zone → move PDFs → write stub `index.md`). The `/ingest` command gains a pre-flight block that runs this script and prompts for tags/notes before proceeding with normal PDF ingest. The linter gains two checks: `drop_zone_not_empty` and coverage of `raw/local/` by the existing PDF index check.

**Tech Stack:** Python 3.10+ stdlib only for `adopt_drop.py`; `python-slugify` for slug generation (already a project dependency). All tests use `pytest` with `tmp_path`.

> **Backlog tracking:** Before executing each task, create a Backlog.md task for it using `mcp__backlog__task_create`. Each task in this plan = one atomic Backlog.md task.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `skills/shared/vault_state.py` | Modify | Add `drop_zone` to `_DEFAULTS` |
| `vault.config.yml` | Modify | Add `drop_zone` section |
| `skills/inbox-fetcher/scripts/adopt_drop.py` | **Create** | New adoption script |
| `tests/test_adopt_drop.py` | **Create** | Tests for adopt_drop.py |
| `tests/test_vault_state.py` | Modify | Tests for new defaults |
| `skills/vault-linter/scripts/lint.py` | Modify | Extend `check_pdf_index`; add `check_drop_zone` |
| `tests/test_lint.py` | Modify | Tests for new lint checks |
| `commands/ingest.md` | Modify | Pre-flight block + `local-pdf` branch |
| `CLAUDE.md` | Modify | Structure diagram, INGEST section, dispatch table, invariant |
| `skills/inbox-fetcher/SKILL.md` | Modify | Document `adopt_drop.py` |
| `skills/vault-linter/SKILL.md` | Modify | Add two new checks to table |
| `init_vault.py` | Modify | Add `raw/local/`, `raw/drop/`, install `adopt_drop.py` |

---

## Task 1: Add `drop_zone` defaults to `vault_state.py` and `vault.config.yml`

**Files:**
- Modify: `skills/shared/vault_state.py` (around line 44)
- Modify: `vault.config.yml` (end of file)
- Modify: `tests/test_vault_state.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_vault_state.py`:

```python
class TestDropZoneDefaults:
    def test_load_config_returns_drop_zone_defaults_when_config_absent(self, tmp_path):
        from vault_state import load_config
        cfg = load_config(tmp_path)
        assert cfg["drop_zone"]["path"] == "raw/drop"
        assert cfg["drop_zone"]["enabled"] is True

    def test_load_config_respects_drop_zone_overrides(self, tmp_path):
        from vault_state import load_config
        (tmp_path / "vault.config.yml").write_text(
            "drop_zone:\n  path: raw/inbox-pdfs\n  enabled: false\n"
        )
        cfg = load_config(tmp_path)
        assert cfg["drop_zone"]["path"] == "raw/inbox-pdfs"
        assert cfg["drop_zone"]["enabled"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_vault_state.py::TestDropZoneDefaults -v
```
Expected: `FAILED` — `KeyError: 'drop_zone'`

- [ ] **Step 3: Add `drop_zone` to `_DEFAULTS` in `vault_state.py`**

In `skills/shared/vault_state.py`, after the `"ingest"` block (line 47), add:

```python
    "drop_zone": {
        "path": "raw/drop",
        "enabled": True,
    },
```

- [ ] **Step 4: Add `drop_zone` section to `vault.config.yml`**

Append to `vault.config.yml`:

```yaml

drop_zone:
  path: "raw/drop"      # relative to vault root
  enabled: true
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_vault_state.py::TestDropZoneDefaults -v
```
Expected: `PASSED`

- [ ] **Step 6: Run the full test suite to check for regressions**

```bash
pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add skills/shared/vault_state.py vault.config.yml tests/test_vault_state.py
git commit -m "feat(config): add drop_zone defaults to vault_state and vault.config.yml"
```

---

## Task 2: `adopt_drop.py` — slug and title helpers

**Files:**
- Create: `skills/inbox-fetcher/scripts/adopt_drop.py`
- Create: `tests/test_adopt_drop.py`

- [ ] **Step 1: Create the test file with slug/title tests**

Create `tests/test_adopt_drop.py`:

```python
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "inbox-fetcher" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))


class TestSlugFromFilename:
    def test_hyphenated_filename(self):
        from adopt_drop import slug_from_filename
        assert slug_from_filename("attention-is-all-you-need.pdf") == "attention-is-all-you-need"

    def test_spaces_become_hyphens(self):
        from adopt_drop import slug_from_filename
        assert slug_from_filename("My Paper 2024.pdf") == "my-paper-2024"

    def test_underscores_become_hyphens(self):
        from adopt_drop import slug_from_filename
        assert slug_from_filename("my_paper_title.pdf") == "my-paper-title"

    def test_returns_non_empty_for_messy_name(self):
        from adopt_drop import slug_from_filename
        slug = slug_from_filename("Final_Paper_v3 (2).pdf")
        assert slug  # non-empty

    def test_no_dots_in_slug(self):
        from adopt_drop import slug_from_filename
        slug = slug_from_filename("paper.v2.pdf")
        assert "." not in slug


class TestTitleFromSlug:
    def test_hyphens_become_spaces_title_cased(self):
        from adopt_drop import title_from_slug
        assert title_from_slug("attention-is-all-you-need") == "Attention Is All You Need"

    def test_single_word(self):
        from adopt_drop import title_from_slug
        assert title_from_slug("transformers") == "Transformers"

    def test_empty_returns_empty(self):
        from adopt_drop import title_from_slug
        assert title_from_slug("") == ""

    def test_underscores_also_become_spaces(self):
        from adopt_drop import title_from_slug
        assert title_from_slug("my_paper") == "My Paper"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_adopt_drop.py::TestSlugFromFilename tests/test_adopt_drop.py::TestTitleFromSlug -v
```
Expected: `ERROR` — `ModuleNotFoundError: No module named 'adopt_drop'`

- [ ] **Step 3: Create `adopt_drop.py` with just the helpers**

Create `skills/inbox-fetcher/scripts/adopt_drop.py`:

```python
#!/usr/bin/env python3
"""
adopt_drop.py — Adopt copy-pasted PDFs from the drop zone into raw/local/.

Usage:
    python3 adopt_drop.py                    # uses current dir as vault
    python3 adopt_drop.py --vault /path      # explicit vault path
    python3 adopt_drop.py --dry-run          # preview without moving

Reads raw/drop/ for .pdf files, moves each into raw/local/<slug>/paper.pdf,
and writes a stub index.md with fetch_method: local-pdf.

Idempotent: skips if raw/local/<slug>/ already exists.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from vault_state import load_config

MISSING_DEPS = []
try:
    from slugify import slugify
except ImportError:
    MISSING_DEPS.append("python-slugify")

if MISSING_DEPS:
    print("Missing dependencies. Install with:", file=sys.stderr)
    print(f"  pip install {' '.join(MISSING_DEPS)}", file=sys.stderr)
    sys.exit(1)


def slug_from_filename(filename: str) -> str:
    """Derive a filesystem-safe slug from a PDF filename stem."""
    stem = Path(filename).stem
    return slugify(stem)


def title_from_slug(slug: str) -> str:
    """Convert a slug to a human-readable title (hyphens/underscores → spaces, title-case)."""
    words = slug.replace("-", " ").replace("_", " ").split()
    return " ".join(w.capitalize() for w in words) if words else slug
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_adopt_drop.py::TestSlugFromFilename tests/test_adopt_drop.py::TestTitleFromSlug -v
```
Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/inbox-fetcher/scripts/adopt_drop.py tests/test_adopt_drop.py
git commit -m "feat(adopt-drop): add slug_from_filename and title_from_slug helpers"
```

---

## Task 3: `adopt_drop.py` — `adopt_pdf` function

**Files:**
- Modify: `skills/inbox-fetcher/scripts/adopt_drop.py` (append)
- Modify: `tests/test_adopt_drop.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_adopt_drop.py`:

```python
class TestAdoptPdf:
    def test_moves_pdf_and_creates_index(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "attention-is-all-you-need.pdf").write_bytes(b"%PDF-1.4 fake")
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)

        result = adopt_pdf(drop / "attention-is-all-you-need.pdf", local)

        assert result.ok
        assert result.slug == "attention-is-all-you-need"
        assert not (drop / "attention-is-all-you-need.pdf").exists()
        assert (local / "attention-is-all-you-need" / "paper.pdf").exists()
        index = (local / "attention-is-all-you-need" / "index.md").read_text()
        assert "fetch_method: local-pdf" in index
        assert "Attention Is All You Need" in index
        assert "source_url" not in index

    def test_index_has_required_frontmatter(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "lecun-path.pdf").write_bytes(b"%PDF")
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)

        adopt_pdf(drop / "lecun-path.pdf", local)

        index = (local / "lecun-path" / "index.md").read_text()
        assert "fetch_method: local-pdf" in index
        assert "title:" in index
        assert "fetched:" in index
        assert "tags: []" in index
        assert "PDF: [[paper.pdf]]" in index

    def test_skips_on_slug_collision(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "my-paper.pdf").write_bytes(b"%PDF")
        local = tmp_path / "raw" / "local"
        (local / "my-paper").mkdir(parents=True)
        (local / "my-paper" / "paper.pdf").write_bytes(b"%PDF existing")

        result = adopt_pdf(drop / "my-paper.pdf", local)

        assert not result.ok
        assert "already exists" in result.reason
        assert (drop / "my-paper.pdf").exists()  # not moved

    def test_dry_run_does_not_move_file(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "my-paper.pdf").write_bytes(b"%PDF")
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)

        result = adopt_pdf(drop / "my-paper.pdf", local, dry_run=True)

        assert result.ok
        assert (drop / "my-paper.pdf").exists()  # not moved
        assert not (local / "my-paper").exists()  # not created
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_adopt_drop.py::TestAdoptPdf -v
```
Expected: `FAILED` — `ImportError` for `AdoptResult` / `adopt_pdf`

- [ ] **Step 3: Add `AdoptResult` dataclass and `adopt_pdf` function**

Append to `skills/inbox-fetcher/scripts/adopt_drop.py` (after `title_from_slug`):

```python
@dataclass
class AdoptResult:
    filename: str
    slug: str
    ok: bool
    reason: str | None = None


def adopt_pdf(pdf_path: Path, local_dir: Path, dry_run: bool = False) -> AdoptResult:
    """Adopt a single PDF from the drop zone into raw/local/<slug>/."""
    slug = slug_from_filename(pdf_path.name)
    if not slug:
        return AdoptResult(filename=pdf_path.name, slug="", ok=False,
                           reason="could not derive a slug from filename")

    out_dir = local_dir / slug
    if out_dir.exists():
        return AdoptResult(filename=pdf_path.name, slug=slug, ok=False,
                           reason=f"raw/local/{slug}/ already exists — skipped")

    if dry_run:
        return AdoptResult(filename=pdf_path.name, slug=slug, ok=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path.rename(out_dir / "paper.pdf")

    title = title_from_slug(slug)
    index_lines = [
        "---",
        "fetch_method: local-pdf",
        f'title: "{title}"',
        f"fetched: {date.today().isoformat()}",
        "tags: []",
        "---",
        "",
        "PDF: [[paper.pdf]]",
        "",
    ]
    (out_dir / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    return AdoptResult(filename=pdf_path.name, slug=slug, ok=True)
```

Also add `from dataclasses import dataclass` to the imports at the top of the file (it's already there from the initial scaffold).

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_adopt_drop.py::TestAdoptPdf -v
```
Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/inbox-fetcher/scripts/adopt_drop.py tests/test_adopt_drop.py
git commit -m "feat(adopt-drop): add AdoptResult dataclass and adopt_pdf function"
```

---

## Task 4: `adopt_drop.py` — `process_drop_zone` orchestrator and CLI

**Files:**
- Modify: `skills/inbox-fetcher/scripts/adopt_drop.py` (append)
- Modify: `tests/test_adopt_drop.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_adopt_drop.py`:

```python
class TestProcessDropZone:
    def test_ignores_non_pdf_files(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "notes.docx").write_bytes(b"fake docx")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        process_drop_zone(tmp_path)

        assert (drop / "notes.docx").exists()
        assert not list((tmp_path / "raw" / "local").iterdir())

    def test_adopts_multiple_pdfs(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper-one.pdf").write_bytes(b"%PDF")
        (drop / "paper-two.pdf").write_bytes(b"%PDF")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 0
        assert (tmp_path / "raw" / "local" / "paper-one" / "paper.pdf").exists()
        assert (tmp_path / "raw" / "local" / "paper-two" / "paper.pdf").exists()

    def test_returns_exit_code_2_when_some_skipped(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "collision.pdf").write_bytes(b"%PDF new")
        local = tmp_path / "raw" / "local"
        (local / "collision").mkdir(parents=True)
        (local / "collision" / "paper.pdf").write_bytes(b"%PDF existing")

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 2

    def test_skips_when_drop_zone_disabled(self, tmp_path):
        from adopt_drop import process_drop_zone
        (tmp_path / "vault.config.yml").write_text(
            "drop_zone:\n  enabled: false\n  path: raw/drop\n"
        )
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper.pdf").write_bytes(b"%PDF")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        process_drop_zone(tmp_path)

        assert (drop / "paper.pdf").exists()  # not moved

    def test_returns_0_when_drop_zone_absent(self, tmp_path):
        from adopt_drop import process_drop_zone
        exit_code = process_drop_zone(tmp_path)
        assert exit_code == 0

    def test_dry_run_does_not_move_any_file(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper.pdf").write_bytes(b"%PDF")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        process_drop_zone(tmp_path, dry_run=True)

        assert (drop / "paper.pdf").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_adopt_drop.py::TestProcessDropZone -v
```
Expected: `FAILED` — `ImportError` for `process_drop_zone`

- [ ] **Step 3: Add `process_drop_zone` and `main` to `adopt_drop.py`**

Append to `skills/inbox-fetcher/scripts/adopt_drop.py`:

```python
def process_drop_zone(vault: Path, dry_run: bool = False) -> int:
    cfg = load_config(vault)
    drop_path = cfg.get("drop_zone", {}).get("path", "raw/drop")
    enabled = cfg.get("drop_zone", {}).get("enabled", True)

    if not enabled:
        print("Drop zone disabled (drop_zone.enabled: false in vault.config.yml).")
        return 0

    drop_dir = vault / drop_path
    if not drop_dir.is_dir():
        print(f"Drop zone not found: {drop_dir}")
        return 0

    local_dir = vault / "raw" / "local"
    local_dir.mkdir(parents=True, exist_ok=True)

    all_files = [p for p in drop_dir.iterdir() if p.is_file()]
    non_pdfs = [p for p in all_files if p.suffix.lower() != ".pdf"]
    pdf_files = [p for p in all_files if p.suffix.lower() == ".pdf"]

    for f in non_pdfs:
        print(f"  ⚠ ignored (not a PDF): {f.name}")

    if not pdf_files:
        print("Drop zone empty. Nothing to adopt.")
        return 0

    print(f"Found {len(pdf_files)} PDF(s) in drop zone.")
    if dry_run:
        for p in pdf_files:
            print(f"  would adopt: {p.name} → raw/local/{slug_from_filename(p.name)}/")
        return 0

    results: list[AdoptResult] = []
    for pdf in pdf_files:
        r = adopt_pdf(pdf, local_dir)
        results.append(r)
        if r.ok:
            print(f"  ✓ adopted  raw/local/{r.slug}/")
        else:
            print(f"  ⚠ {r.reason}")

    n_ok = sum(1 for r in results if r.ok)
    n_skip = sum(1 for r in results if not r.ok)
    print()
    print(f"Adopted {n_ok}, skipped {n_skip}.")

    return 0 if n_skip == 0 else 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Adopt PDFs from the drop zone into raw/local/."
    )
    parser.add_argument(
        "--vault", type=Path, default=Path.cwd(),
        help="Path to vault root (default: current directory).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List files that would be adopted without moving them.",
    )
    args = parser.parse_args()

    if not args.vault.is_dir():
        print(f"ERROR: vault path is not a directory: {args.vault}", file=sys.stderr)
        return 1

    return process_drop_zone(args.vault, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_adopt_drop.py::TestProcessDropZone -v
```
Expected: all `PASSED`

- [ ] **Step 5: Run the full adopt_drop test suite**

```bash
pytest tests/test_adopt_drop.py -v
```
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add skills/inbox-fetcher/scripts/adopt_drop.py tests/test_adopt_drop.py
git commit -m "feat(adopt-drop): add process_drop_zone orchestrator and CLI entry point"
```

---

## Task 5: `lint.py` — extend `check_pdf_index` to cover `raw/local/`

**Files:**
- Modify: `skills/vault-linter/scripts/lint.py` (lines 343–369)
- Modify: `tests/test_lint.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_lint.py`:

```python
class TestCheckLocalIndex:
    def test_no_findings_when_local_dir_absent(self, tmp_path):
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_advisory_for_local_subdir_without_index(self, tmp_path):
        slug = tmp_path / "raw" / "local" / "my-paper"
        slug.mkdir(parents=True)
        (slug / "paper.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        assert any(f.check == "missing_pdf_index" for f in findings)
        assert all(f.severity == "advisory" for f in findings)

    def test_no_findings_for_correct_local_structure(self, tmp_path):
        slug = tmp_path / "raw" / "local" / "my-paper"
        slug.mkdir(parents=True)
        (slug / "paper.pdf").write_bytes(b"%PDF")
        (slug / "index.md").write_text("---\nfetch_method: local-pdf\n---\n")
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_advisory_for_flat_pdf_in_local(self, tmp_path):
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)
        (local / "orphan.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        assert any(f.check == "legacy_flat_pdf" for f in findings)

    def test_checks_both_papers_and_local(self, tmp_path):
        (tmp_path / "raw" / "papers" / "p1").mkdir(parents=True)
        (tmp_path / "raw" / "papers" / "p1" / "paper.pdf").write_bytes(b"%PDF")
        (tmp_path / "raw" / "local" / "p2").mkdir(parents=True)
        (tmp_path / "raw" / "local" / "p2" / "paper.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        files = [f.file for f in findings]
        assert any("papers" in fp for fp in files)
        assert any("local" in fp for fp in files)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_lint.py::TestCheckLocalIndex -v
```
Expected: `FAILED` — `raw/local/` not checked

- [ ] **Step 3: Rewrite `check_pdf_index` in `lint.py`**

Replace the existing `check_pdf_index` function (lines 343–369) with:

```python
def check_pdf_index(vault: Path) -> list[Finding]:
    """
    Verify that raw/papers/ and raw/local/ follow the folder convention:
    each paper lives in its own subdirectory with a companion index.md.
    """
    findings = []
    for folder_name in ("papers", "local"):
        folder = vault / "raw" / folder_name
        if not folder.is_dir():
            continue
        for entry in folder.iterdir():
            if entry.is_dir():
                if not (entry / "index.md").exists():
                    findings.append(Finding(
                        severity="advisory",
                        check="missing_pdf_index",
                        file=str(entry.relative_to(vault)),
                        detail=f"raw/{folder_name}/ subdirectory has no index.md",
                    ))
            elif entry.suffix.lower() == ".pdf":
                findings.append(Finding(
                    severity="advisory",
                    check="legacy_flat_pdf",
                    file=str(entry.relative_to(vault)),
                    detail=f"flat .pdf in raw/{folder_name}/ — move into a <slug>/ subdirectory",
                ))
    return findings
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_lint.py::TestCheckPdfIndex tests/test_lint.py::TestCheckLocalIndex -v
```
Expected: all `PASSED` (existing `TestCheckPdfIndex` tests must still pass)

- [ ] **Step 5: Commit**

```bash
git add skills/vault-linter/scripts/lint.py tests/test_lint.py
git commit -m "feat(lint): extend check_pdf_index to cover raw/local/ folder"
```

---

## Task 6: `lint.py` — add `check_drop_zone` check

**Files:**
- Modify: `skills/vault-linter/scripts/lint.py` (after `check_pdf_index`, and `run_lint`)
- Modify: `tests/test_lint.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_lint.py`:

```python
class TestCheckDropZone:
    def test_no_findings_when_drop_zone_absent(self, tmp_path):
        from lint import check_drop_zone
        assert check_drop_zone(tmp_path) == []

    def test_no_findings_when_drop_zone_empty(self, tmp_path):
        (tmp_path / "raw" / "drop").mkdir(parents=True)
        from lint import check_drop_zone
        assert check_drop_zone(tmp_path) == []

    def test_advisory_when_pdf_present(self, tmp_path):
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "unprocessed.pdf").write_bytes(b"%PDF")
        from lint import check_drop_zone
        findings = check_drop_zone(tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "drop_zone_not_empty"
        assert findings[0].severity == "advisory"

    def test_detail_mentions_count(self, tmp_path):
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "a.pdf").write_bytes(b"%PDF")
        (drop / "b.pdf").write_bytes(b"%PDF")
        from lint import check_drop_zone
        findings = check_drop_zone(tmp_path)
        assert "2" in findings[0].detail

    def test_ignores_non_pdf_files(self, tmp_path):
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "notes.txt").write_text("just a note")
        from lint import check_drop_zone
        assert check_drop_zone(tmp_path) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_lint.py::TestCheckDropZone -v
```
Expected: `FAILED` — `ImportError` for `check_drop_zone`

- [ ] **Step 3: Add `check_drop_zone` function to `lint.py`**

In `skills/vault-linter/scripts/lint.py`, add after the `check_pdf_index` function:

```python
def check_drop_zone(vault: Path) -> list[Finding]:
    """Advisory check: PDFs in the drop zone have not been adopted yet."""
    cfg = load_config(vault)
    drop_path = cfg.get("drop_zone", {}).get("path", "raw/drop")
    drop_dir = vault / drop_path
    if not drop_dir.is_dir():
        return []
    pdfs = [
        p for p in drop_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".pdf"
    ]
    if not pdfs:
        return []
    return [Finding(
        severity="advisory",
        check="drop_zone_not_empty",
        file=str(drop_dir.relative_to(vault)),
        detail=f"Drop zone has {len(pdfs)} unprocessed file(s) — run /ingest to adopt them.",
    )]
```

- [ ] **Step 4: Wire `check_drop_zone` into `run_lint`**

In `run_lint`, in the `all_checks` list (around line 751), add after the `"conversations"` entry:

```python
        ("drop_zone", check_drop_zone),
```

Also, in the dispatch block (around line 771), the existing condition:
```python
elif name in ("pdf_index", "conversations"):
    out = fn(vault)
```
Must become:
```python
elif name in ("pdf_index", "conversations", "drop_zone"):
    out = fn(vault)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_lint.py::TestCheckDropZone -v
```
Expected: all `PASSED`

- [ ] **Step 6: Run the full test suite**

```bash
pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add skills/vault-linter/scripts/lint.py tests/test_lint.py
git commit -m "feat(lint): add check_drop_zone advisory check for unadopted PDFs"
```

---

## Task 7: `commands/ingest.md` — pre-flight block and `local-pdf` branch

**Files:**
- Modify: `commands/ingest.md`

- [ ] **Step 1: Add the pre-flight section**

In `commands/ingest.md`, insert the following block **before** the existing `## Discover targets` section:

```markdown
## Pre-flight: drop zone adoption

Before discovering uningested sources, check whether the drop zone contains
any PDFs waiting to be adopted.

1. Read `drop_zone.path` from `vault.config.yml` (default: `raw/drop`).
2. Scan for `*.pdf` files in the drop zone directory.
3. If any are found:
   a. Run: `python3 skills/inbox-fetcher/scripts/adopt_drop.py --vault <vault_root>`
   b. Report: "Adopted N PDF(s): [slug, slug, ...]"
   c. Ask once (batch prompt):
      > "Any tags or focus notes before I ingest these?
      > Example: `lecun-path: tags: autonomy, ml | note: focus on world models`"
   d. If the user provides tags or notes, update each affected
      `raw/local/<slug>/index.md` frontmatter before reading the PDF.
4. Proceed — newly adopted slugs now appear as uningested sources in
   `raw/local/` and will be discovered in the step below.

If `drop_zone.enabled: false` in `vault.config.yml`, skip this step silently.
```

- [ ] **Step 2: Extend the PDF ingest protocol with the `local-pdf` branch**

In `commands/ingest.md`, under `### PDFs`, extend step 1 and add a note after step 4:

Replace the existing `### PDFs` section with:

```markdown
### PDFs

Source: `raw/papers/<slug>/index.md` with `fetch_method: pdf`, **or**
`raw/local/<slug>/index.md` with `fetch_method: local-pdf`.

1. Read `index.md` — get `title`, `tags`, `note`.
   - For `fetch_method: pdf`: also read `source_url`.
   - For `fetch_method: local-pdf`: no `source_url` field; omit it everywhere.
2. Read `paper.pdf` using the Read tool — pages 1–5. If the paper has more than
   10 pages, also read the last 2 pages.
3. Infer the title from the first visible heading; fall back to the `title` in
   `index.md` frontmatter.
4. Write `wiki/sources/<slug>.md` with the same schema as web sources.
   - For `fetch_method: pdf`: include `source_path: raw/papers/<slug>/`.
   - For `fetch_method: local-pdf`: include `source_path: raw/local/<slug>/`.
     Do **not** include a `source_url` field.
5. Propagate `tags` and `note` as with other source types.
```

- [ ] **Step 3: Commit**

```bash
git add commands/ingest.md
git commit -m "feat(ingest): add drop zone pre-flight block and local-pdf protocol branch"
```

---

## Task 8: `CLAUDE.md` — update structure, INGEST, dispatch, invariant

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the vault structure diagram**

In `CLAUDE.md`, find the vault structure block under `## Vault structure`. The `raw/` lines currently show:

```
  raw/                  Immutable sources. Never write here.
    papers/             PDFs
    web/<slug>/         Web articles converted to markdown
```

Replace with:

```
  raw/                  Immutable sources. Never write here.
    papers/             PDFs fetched via URL
    web/<slug>/         Web articles converted to markdown
    local/<slug>/       PDFs copy-pasted by the user
    drop/               Drop zone — paste PDFs here; emptied by /ingest
```

- [ ] **Step 2: Update invariant #1 note**

In `CLAUDE.md`, find invariant #1:

```
1. **Never write to `raw/`.** Only the fetcher skill adds files there.
```

Replace with:

```
1. **Never write to `raw/`.** Only scripts add files there: `fetch_inbox.py`
   writes to `raw/papers/` and `raw/web/`; `adopt_drop.py` writes to
   `raw/local/`. The LLM never writes to `raw/`.
```

- [ ] **Step 3: Add `local-pdf` source type branch to INGEST**

In `CLAUDE.md`, under `### INGEST — source type branches`, add a new branch after the existing `**PDFs**` branch:

```markdown
**Local PDFs** (`raw/local/<slug>/index.md`, `fetch_method: local-pdf`):
1. Read `index.md` — get `title`, `tags`, `note`. There is no `source_url`.
2. Read `paper.pdf` pages 1–5 (same as URL-fetched PDFs).
3. Write `wiki/sources/<slug>.md` — omit the `source_url` field entirely.
   Use `source_path: raw/local/<slug>/` in frontmatter.
4. Carry `tags` and `note` as with other source types.
```

- [ ] **Step 4: Add ADOPT row to the skill dispatch table**

In `CLAUDE.md`, find the `## Skill dispatch` table. Add a row:

```
| ADOPT     | adopt_drop.py  | scripts/adopt_drop.py          |
```

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): add drop zone to structure, invariant, INGEST, dispatch table"
```

---

## Task 9: `skills/inbox-fetcher/SKILL.md` — document `adopt_drop.py`

**Files:**
- Modify: `skills/inbox-fetcher/SKILL.md`

- [ ] **Step 1: Update the description frontmatter**

In `skills/inbox-fetcher/SKILL.md`, update the `description:` field in frontmatter to append:

> Also provides `adopt_drop.py`, which adopts copy-pasted PDFs from `raw/drop/` into `raw/local/<slug>/` as a pre-flight step for `/ingest`.

- [ ] **Step 2: Add a new `## Drop zone adoption` section**

Add the following section before `## Not in scope`:

```markdown
## Drop zone adoption (`adopt_drop.py`)

Companion script for copy-pasted PDFs that arrive outside a URL.

**When to use:** called automatically by `/ingest` as a pre-flight step
when `raw/drop/` (or the configured `drop_zone.path`) contains `.pdf` files.

**What it does per file:**
1. Derives a slug from the filename stem via `slugify()`.
2. Checks for collision: if `raw/local/<slug>/` already exists, skips with a warning.
3. Creates `raw/local/<slug>/`, moves the PDF to `paper.pdf`.
4. Writes a stub `index.md` with `fetch_method: local-pdf`, stub title, and today's date.
5. Prints `✓ adopted raw/local/<slug>/`.

**Run manually:**
```bash
python3 skills/inbox-fetcher/scripts/adopt_drop.py --vault .
python3 skills/inbox-fetcher/scripts/adopt_drop.py --dry-run
```

**Output contract:**
```
Found 2 PDF(s) in drop zone.
  ✓ adopted  raw/local/attention-is-all-you-need/
  ✓ adopted  raw/local/lecun-path-to-autonomy/
Adopted 2, skipped 0.
```

Exit codes: `0` = all adopted; `2` = partial (some skipped due to collisions).
```

- [ ] **Step 3: Commit**

```bash
git add skills/inbox-fetcher/SKILL.md
git commit -m "docs(inbox-fetcher): document adopt_drop.py in SKILL.md"
```

---

## Task 10: `skills/vault-linter/SKILL.md` — add new checks to table

**Files:**
- Modify: `skills/vault-linter/SKILL.md`

- [ ] **Step 1: Update the description frontmatter**

In `skills/vault-linter/SKILL.md`, update the `description:` field to change "Thirteen deterministic checks" to "Fifteen deterministic checks" and append the two new check names to the description string.

- [ ] **Step 2: Update the checks table**

Find the checks table in `## What it checks`. Change the header row from `Thirteen deterministic checks` to `Fifteen deterministic checks`, and append two rows:

```markdown
| 14 | **Local PDF index integrity** | `raw/local/` subdir missing `index.md`, or legacy flat `.pdf` in `raw/local/` |
| 15 | **Drop zone not empty** | PDFs waiting in `raw/drop/` that haven't been adopted by `/ingest` |
```

Also update check #11 label from `**PDF index integrity**` to `**Papers PDF index integrity**` to clarify it covers `raw/papers/` specifically (and check #14 covers `raw/local/`).

- [ ] **Step 3: Update "Fourteen deterministic checks" prose reference**

Search the file for any prose references to "Thirteen" and update to "Fifteen".

- [ ] **Step 4: Commit**

```bash
git add skills/vault-linter/SKILL.md
git commit -m "docs(vault-linter): add checks 14 and 15 to SKILL.md table"
```

---

## Task 11: `init_vault.py` — add `raw/local/`, `raw/drop/`, install `adopt_drop.py`

**Files:**
- Modify: `init_vault.py`

- [ ] **Step 1: Add `raw/local` and `raw/drop` to `DIRS` and `GITKEEP_DIRS`**

In `init_vault.py`, find the `DIRS` list (line 63). Add two entries:

```python
DIRS = [
    "raw/papers",
    "raw/web",
    "raw/local",   # ← add
    "raw/drop",    # ← add
    ...
]
```

Find the `GITKEEP_DIRS` list (line 79). Add two entries:

```python
GITKEEP_DIRS = [
    "raw/papers", "raw/web", "raw/local", "raw/drop",  # ← add both
    "wiki/pages", "wiki/sources",
    ...
]
```

- [ ] **Step 2: Add `adopt_drop.py` to `install_skills`**

In `init_vault.py`, find the `install_skills` function and the `inbox-fetcher` entry (around line 314):

```python
    for skill_name, py_scripts in [
        ("inbox-fetcher", ["scripts/fetch_inbox.py"]),
```

Change to:

```python
    for skill_name, py_scripts in [
        ("inbox-fetcher", ["scripts/fetch_inbox.py", "scripts/adopt_drop.py"]),
```

- [ ] **Step 3: Update the `print_done` banner**

In `init_vault.py`, find the `print_done` function. The line:

```python
    print( "  2. Add URLs to inbox.md (or drop PDFs in raw/papers/)")
```

Change to:

```python
    print( "  2. Add URLs to inbox.md, or drop PDFs in raw/drop/")
```

- [ ] **Step 4: Verify the changes manually**

```bash
python3 init_vault.py --here --help
```
Expected: no errors, help text shown.

Run a dry check of the install paths:

```bash
python3 -c "
import init_vault
from pathlib import Path
print('raw/local' in init_vault.DIRS)
print('raw/drop' in init_vault.DIRS)
print('scripts/adopt_drop.py' in init_vault.install_skills.__code__.co_consts or True)
"
```
Expected: `True`, `True`, `True` (the last check is approximate; visually verify the list instead).

- [ ] **Step 5: Commit**

```bash
git add init_vault.py
git commit -m "feat(init): create raw/local/ and raw/drop/ dirs, install adopt_drop.py"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Covered by task |
|---|---|
| `raw/drop/` drop zone | Tasks 1, 4, 6, 8, 11 |
| `raw/local/<slug>/` storage | Tasks 3, 5, 8, 11 |
| `adopt_drop.py` scaffold script | Tasks 2, 3, 4, 9 |
| Slug from filename | Task 2 |
| Stub `index.md` with `fetch_method: local-pdf` | Task 3 |
| Collision skip | Task 3 |
| Non-PDF ignored | Task 4 |
| `drop_zone` config section | Task 1 |
| `/ingest` pre-flight block | Task 7 |
| `/ingest` interactive tags/notes prompt | Task 7 |
| `/ingest` `local-pdf` branch (no `source_url`) | Tasks 7, 8 |
| Linter: `DROP_ZONE_NOT_EMPTY` | Task 6 |
| Linter: extend `PAPERS_MISSING_INDEX` to `raw/local/` | Task 5 |
| `CLAUDE.md` updates | Task 8 |
| `inbox-fetcher/SKILL.md` update | Task 9 |
| `vault-linter/SKILL.md` update | Task 10 |
| `init_vault.py` updates | Task 11 |

All spec requirements covered. ✓

**Type consistency check:** `AdoptResult`, `slug_from_filename`, `title_from_slug`, `adopt_pdf`, `process_drop_zone` are defined in Task 2/3/4 and referenced consistently in Task 4's tests. `check_drop_zone` defined in Task 6, wired in Task 6. No cross-task name mismatches. ✓

**Placeholder scan:** No TBDs or incomplete steps. ✓
