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
import json
import re
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
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
    if out_dir.is_dir():
        return AdoptResult(filename=pdf_path.name, slug=slug, ok=False,
                           reason=f"raw/local/{slug}/ already exists - skipped")

    if dry_run:
        return AdoptResult(filename=pdf_path.name, slug=slug, ok=True)

    out_dir.mkdir(parents=True, exist_ok=True)

    title = title_from_slug(slug)
    index_lines = [
        "---",
        "fetch_method: local-pdf",
        f"title: {json.dumps(title)}",
        f"fetched: {date.today().isoformat()}",
        "tags: []",
        "---",
        "",
        "PDF: [[paper.pdf]]",
        "",
    ]
    index_path = out_dir / "index.md"
    try:
        index_path.write_text("\n".join(index_lines), encoding="utf-8")
    except Exception:
        # index.md write failed before PDF moved — clean up dir only, no rename needed.
        index_path.unlink(missing_ok=True)
        out_dir.rmdir()
        raise

    try:
        # shutil.move handles cross-filesystem moves transparently;
        # Path.rename() raises OSError on cross-device moves.
        shutil.move(str(pdf_path), str(out_dir / "paper.pdf"))
    except Exception:
        # move failed after index.md written — undo index and dir.
        index_path.unlink(missing_ok=True)
        out_dir.rmdir()
        raise

    return AdoptResult(filename=pdf_path.name, slug=slug, ok=True)


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
        f"title: {json.dumps(title)}",
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
        # shutil.move handles cross-filesystem moves transparently;
        # Path.rename() raises OSError on cross-device moves.
        shutil.move(str(md_path), str(out_dir / "content.md"))
    except Exception:
        index_path.unlink(missing_ok=True)
        out_dir.rmdir()
        raise

    return AdoptResult(filename=md_path.name, slug=slug, ok=True)


HANDLERS: dict[str, Callable[[Path, Path, bool], AdoptResult]] = {
    ".pdf": adopt_pdf,
    ".md":  adopt_md,
}


def process_drop_zone(vault: Path, dry_run: bool = False) -> int:
    cfg = load_config(vault)
    dz = cfg["drop_zone"]
    drop_path = dz["path"]
    enabled = dz["enabled"]

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
    supported   = [f for f in all_files if f.suffix.lower() in HANDLERS]
    unsupported = [f for f in all_files if f.suffix.lower() not in HANDLERS]

    for f in unsupported:
        print(f"  [!] ignored (unsupported type): {f.name}")

    if not supported:
        print("Drop zone empty. Nothing to adopt.")
        return 0

    _TYPE_ORDER = [".pdf", ".md"]   # display priority: PDF first
    type_labels = {".pdf": "PDF", ".md": "Markdown"}
    counts: dict[str, int] = {}
    for f in supported:
        ext = f.suffix.lower()
        counts[ext] = counts.get(ext, 0) + 1
    parts = [f"{counts[e]} {type_labels[e]}(s)" for e in _TYPE_ORDER if e in counts]
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
