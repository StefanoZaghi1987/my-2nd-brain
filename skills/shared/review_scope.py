#!/usr/bin/env python3
"""
review_scope.py — Enumerate wiki pages modified since the last REVIEW run.

Used by the /review command to determine the default scope: only pages
whose frontmatter `updated` date is strictly after `last_review` in
.review/state.yaml. Uses a self-contained frontmatter parser so this
script can run as a standalone utility regardless of where the other
skill scripts live.

Usage:
    python review_scope.py <vault_root> [--since YYYY-MM-DD]

Exit codes:
    0 — pages found (list to stdout, one path per line)
    1 — no pages in scope
    2 — error (vault not found, bad date, etc.)
"""
from __future__ import annotations
import sys
import re
from pathlib import Path
from datetime import date


def _parse_updated(text: str) -> date | None:
    """Extract the `updated: YYYY-MM-DD` field from YAML frontmatter."""
    m = re.search(r"^updated:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def get_changed_pages(vault: Path, last_review: date | None) -> list[Path]:
    """Return wiki pages updated strictly after last_review.

    Returns all pages when last_review is None (first run).
    Returns a sorted list of Path objects.
    """
    pages_dir = vault / "wiki" / "pages"
    if not pages_dir.exists():
        return []

    result = []
    for page in pages_dir.rglob("*.md"):
        if page.name.startswith("."):
            continue
        if last_review is None:
            # First run — all pages are in scope
            result.append(page)
            continue
        updated = _parse_updated(page.read_text(encoding="utf-8", errors="ignore"))
        if updated is not None and updated > last_review:
            result.append(page)
    return sorted(result)


def _read_last_review(vault: Path) -> date | None:
    """Read last_review from .review/state.yaml. Returns None if absent or null."""
    state_path = vault / ".review" / "state.yaml"
    if not state_path.exists():
        return None
    m = re.search(r"^last_review:\s*(\d{4}-\d{2}-\d{2})",
                  state_path.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="List wiki pages in REVIEW scope.")
    parser.add_argument("vault", help="Vault root path")
    parser.add_argument("--since", help="Override last_review date (YYYY-MM-DD)",
                        default=None)
    args = parser.parse_args()

    vault = Path(args.vault)
    if not vault.is_dir():
        print(f"ERROR: vault not found: {vault}", file=sys.stderr)
        return 2

    if args.since:
        try:
            last_review: date | None = date.fromisoformat(args.since)
        except ValueError:
            print(f"ERROR: invalid date format: {args.since}", file=sys.stderr)
            return 2
    else:
        last_review = _read_last_review(vault)

    pages = get_changed_pages(vault, last_review)
    if not pages:
        return 1
    for p in pages:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
