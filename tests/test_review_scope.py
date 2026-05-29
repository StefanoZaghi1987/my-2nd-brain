"""Tests for review_scope.py — page scoping for the REVIEW operation."""
import sys
from pathlib import Path
from datetime import date
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from review_scope import get_changed_pages


def _write_page(path: Path, updated: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: page\ncreated: 2026-01-01\nupdated: {updated}\ntags: []\n---\n\nContent.\n",
        encoding="utf-8",
    )


def test_returns_all_pages_when_no_prior_review(tmp_path):
    """With last_review=null, every wiki page is in scope."""
    wiki = tmp_path / "wiki" / "pages"
    _write_page(wiki / "page-a.md", "2026-01-01")
    _write_page(wiki / "page-b.md", "2026-03-15")

    result = get_changed_pages(tmp_path, last_review=None)
    names = {p.name for p in result}
    assert names == {"page-a.md", "page-b.md"}


def test_filters_to_pages_newer_than_last_review(tmp_path):
    """Only pages updated after last_review are returned."""
    wiki = tmp_path / "wiki" / "pages"
    _write_page(wiki / "old.md", "2026-01-01")
    _write_page(wiki / "recent.md", "2026-05-20")

    result = get_changed_pages(tmp_path, last_review=date(2026, 3, 1))
    names = {p.name for p in result}
    assert "recent.md" in names
    assert "old.md" not in names


def test_returns_empty_when_nothing_changed(tmp_path):
    """Returns empty list when no pages were updated after last_review."""
    wiki = tmp_path / "wiki" / "pages"
    _write_page(wiki / "stale.md", "2026-01-01")

    result = get_changed_pages(tmp_path, last_review=date(2026, 6, 1))
    assert result == []
