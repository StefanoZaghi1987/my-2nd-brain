#!/usr/bin/env python3
"""
find_backlinks.py — Enumerate all wiki pages that link to a given target page.

Used by the MERGE operation to find every page that must be updated when a
source page is merged into a destination page. Backlink resolution uses the
same normalize_link_target logic as the vault linter.

Scope note: the scan covers the **entire file content**, including YAML
frontmatter. This means links in frontmatter fields such as ``based_on:``
in views are also captured. The result set is therefore a **superset** of
what ``check_dead_links`` in lint.py would flag — lint.py only tracks
wikilinks in body prose, not frontmatter. Callers should be aware of this
when deciding which files need rewriting.

Usage:
    python find_backlinks.py <vault_root> <target_page_path>

Exit codes:
    0 — backlinks found (list to stdout, one path per line)
    1 — no backlinks found
    2 — error (vault not found, target not found, etc.)
"""
from __future__ import annotations
import sys
from pathlib import Path

# The shared directory is not on sys.path by default when invoked standalone;
# insert it so the import below resolves regardless of cwd.
sys.path.insert(0, str(Path(__file__).parent))
from linkutil import WIKILINK_RE, normalize_link_target


def find_backlinks(vault: Path, target: Path) -> list[Path]:
    """Return all wiki pages that contain a wikilink resolving to target.

    Scans the **full content** of every .md file under wiki/ (including
    frontmatter) and checks whether any [[link]] resolves to the same
    filesystem path as target. Because frontmatter is included, the result
    set is a superset of what lint.py's ``check_dead_links`` would flag —
    views with ``based_on: [[wiki/pages/foo]]`` entries are captured here
    but not by the linter's dead-link check.

    Self-referential links (a page linking to itself) are included in the
    results. The MERGE operation must filter the page being merged away
    from the returned list before rewriting, since that page will be deleted.

    Args:
        vault:  Vault root directory (contains wiki/, raw/, etc.).
        target: The page being searched for — any Path accepted; resolved
                internally to an absolute path.

    Returns:
        Sorted list of Path objects for every file that links to target.
        Empty list if none found or wiki/ does not exist.
    """
    target = target.resolve()
    results: list[Path] = []
    wiki_dir = vault / "wiki"
    if not wiki_dir.exists():
        return []
    for page in wiki_dir.rglob("*.md"):
        if page.name.startswith("."):
            continue
        try:
            text = page.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in WIKILINK_RE.finditer(text):
            raw_target = m.group(1)
            resolved = normalize_link_target(raw_target, vault, page)
            if resolved is not None and resolved.resolve() == target:
                results.append(page)
                break  # one match per file is enough
    return sorted(results)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: find_backlinks.py <vault_root> <target_page_path>", file=sys.stderr)
        return 2
    vault = Path(sys.argv[1])
    target = Path(sys.argv[2])
    if not vault.is_dir():
        print(f"ERROR: vault not found: {vault}", file=sys.stderr)
        return 2
    if not target.exists():
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        return 2
    results = find_backlinks(vault, target)
    if not results:
        return 1
    for r in results:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
