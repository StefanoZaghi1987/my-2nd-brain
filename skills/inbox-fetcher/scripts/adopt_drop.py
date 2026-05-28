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
    try:
        (out_dir / "index.md").write_text("\n".join(index_lines), encoding="utf-8")
    except Exception:
        # Roll back: restore PDF to original location, remove empty directory.
        (out_dir / "paper.pdf").rename(pdf_path)
        out_dir.rmdir()
        raise

    return AdoptResult(filename=pdf_path.name, slug=slug, ok=True)
