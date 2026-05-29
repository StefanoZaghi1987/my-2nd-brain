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


def test_excludes_page_updated_on_same_day_as_last_review(tmp_path):
    """A page updated on exactly last_review day is NOT in scope (strictly after)."""
    wiki = tmp_path / "wiki" / "pages"
    _write_page(wiki / "same-day.md", "2026-03-01")

    result = get_changed_pages(tmp_path, last_review=date(2026, 3, 1))
    assert result == []


def test_returns_empty_when_nothing_changed(tmp_path):
    """Returns empty list when no pages were updated after last_review."""
    wiki = tmp_path / "wiki" / "pages"
    _write_page(wiki / "stale.md", "2026-01-01")

    result = get_changed_pages(tmp_path, last_review=date(2026, 6, 1))
    assert result == []


def test_body_prose_updated_date_is_ignored(tmp_path):
    """A page with 'updated: 2026-05-15' ONLY in its body must NOT be mis-dated."""
    wiki = tmp_path / "wiki" / "pages"
    wiki.mkdir(parents=True)
    # Frontmatter has NO updated field; body has a misleading one at line start
    # This is a RECENT date that WOULD be included if parsed from the body
    (wiki / "tricky.md").write_text(
        "---\ntype: page\ncreated: 2026-01-01\ntags: []\n---\n\n"
        "updated: 2026-05-15\n\nThis is body text with a misleading updated field.\n",
        encoding="utf-8",
    )
    # last_review is 2026-01-01 — if body date were used, page WOULD be in scope
    # (2026-05-15 > 2026-01-01). But no frontmatter updated → None → page excluded.
    result = get_changed_pages(tmp_path, last_review=date(2026, 1, 1))
    assert result == [], (
        "A page with updated: only in prose should not be mis-dated"
    )


def test_frontmatter_updated_date_is_used(tmp_path):
    """When frontmatter has 'updated', that date is used correctly."""
    wiki = tmp_path / "wiki" / "pages"
    wiki.mkdir(parents=True)
    (wiki / "normal.md").write_text(
        "---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-05-01\ntags: []\n---\n\n"
        "Body text with no dates.\n",
        encoding="utf-8",
    )
    result = get_changed_pages(tmp_path, last_review=date(2026, 1, 1))
    assert len(result) == 1
    assert result[0].name == "normal.md"
