"""Tests for find_backlinks.py — backlink enumeration for the MERGE operation."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from find_backlinks import find_backlinks


def _make_page(path: Path, links: list[str]) -> None:
    """Write a minimal wiki page with the given [[wikilinks]]."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"See [[{lnk}]]." for lnk in links)
    path.write_text(
        f"---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-01-01\ntags: []\n---\n\n{body}\n",
        encoding="utf-8",
    )


def test_finds_direct_match(tmp_path):
    """A page that links to the target is returned."""
    target = tmp_path / "wiki" / "pages" / "alpha.md"
    linker = tmp_path / "wiki" / "pages" / "beta.md"
    _make_page(target, [])
    _make_page(linker, ["wiki/pages/alpha"])
    result = find_backlinks(tmp_path, target)
    assert linker in result


def test_finds_match_via_md_extension(tmp_path):
    """Links written as [[wiki/pages/alpha.md]] resolve to the same target."""
    target = tmp_path / "wiki" / "pages" / "alpha.md"
    linker = tmp_path / "wiki" / "pages" / "gamma.md"
    _make_page(target, [])
    _make_page(linker, ["wiki/pages/alpha.md"])
    result = find_backlinks(tmp_path, target)
    assert linker in result


def test_no_false_positives(tmp_path):
    """Pages that don't link to the target are not returned."""
    target = tmp_path / "wiki" / "pages" / "alpha.md"
    unrelated = tmp_path / "wiki" / "pages" / "delta.md"
    _make_page(target, [])
    _make_page(unrelated, ["wiki/pages/other"])
    result = find_backlinks(tmp_path, target)
    assert unrelated not in result


def test_multiple_files_linking_same_target(tmp_path):
    """All files linking to the target are returned."""
    target = tmp_path / "wiki" / "pages" / "hub.md"
    a = tmp_path / "wiki" / "pages" / "a.md"
    b = tmp_path / "wiki" / "pages" / "b.md"
    c = tmp_path / "wiki" / "sources" / "s.md"
    _make_page(target, [])
    _make_page(a, ["wiki/pages/hub"])
    _make_page(b, ["wiki/pages/hub"])
    _make_page(c, ["wiki/pages/hub"])
    result = find_backlinks(tmp_path, target)
    assert len(result) == 3
    assert a in result and b in result and c in result


def test_dot_containing_slug(tmp_path):
    """Slugs containing dots (e.g. arxiv IDs) are resolved correctly."""
    target = tmp_path / "wiki" / "sources" / "arxiv-2602.20867.md"
    linker = tmp_path / "wiki" / "pages" / "ref.md"
    _make_page(target, [])
    _make_page(linker, ["wiki/sources/arxiv-2602.20867"])
    result = find_backlinks(tmp_path, target)
    assert linker in result


def test_returns_empty_when_no_backlinks(tmp_path):
    """Returns empty list when nothing links to the target."""
    target = tmp_path / "wiki" / "pages" / "orphan.md"
    _make_page(target, [])
    result = find_backlinks(tmp_path, target)
    assert result == []


def test_finds_aliased_link(tmp_path):
    """[[wiki/pages/alpha|Display Name]] is a backlink to alpha."""
    target = tmp_path / "wiki" / "pages" / "alpha.md"
    linker = tmp_path / "wiki" / "pages" / "epsilon.md"
    _make_page(target, [])
    linker.parent.mkdir(parents=True, exist_ok=True)
    linker.write_text(
        "---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-01-01\ntags: []\n---\n\n"
        "See [[wiki/pages/alpha|Alpha display]].\n", encoding="utf-8")
    assert linker in find_backlinks(tmp_path, target)


def test_self_link_included(tmp_path):
    """A page linking to itself appears in the backlinks.

    NOTE: The MERGE operation must filter the page being merged-away (target)
    from the backlink results before rewriting, since that page will be deleted.
    """
    target = tmp_path / "wiki" / "pages" / "hub.md"
    _make_page(target, ["wiki/pages/hub"])  # links to itself
    result = find_backlinks(tmp_path, target)
    assert target in result
