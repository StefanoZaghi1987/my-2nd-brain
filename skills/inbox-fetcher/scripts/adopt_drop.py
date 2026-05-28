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
                           reason=f"raw/local/{slug}/ already exists - skipped")

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
    non_pdfs = [p for p in all_files if p.suffix.lower() != ".pdf"]
    pdf_files = [p for p in all_files if p.suffix.lower() == ".pdf"]

    for f in non_pdfs:
        print(f"  [!] ignored (not a PDF): {f.name}")

    if not pdf_files:
        print("Drop zone empty. Nothing to adopt.")
        return 0

    print(f"Found {len(pdf_files)} PDF(s) in drop zone.")
    if dry_run:
        for p in pdf_files:
            print(f"  would adopt: {p.name} -> raw/local/{slug_from_filename(p.name)}/")
        return 0

    results: list[AdoptResult] = []
    for pdf in pdf_files:
        r = adopt_pdf(pdf, local_dir, dry_run=dry_run)
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
