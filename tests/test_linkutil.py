"""Tests for the shared link-resolution module (linkutil.py)."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from linkutil import WIKILINK_RE, normalize_link_target


class TestWikilinkRe:
    def test_bare_link(self):
        m = WIKILINK_RE.search("See [[wiki/pages/foo]].")
        assert m is not None
        assert m.group(1) == "wiki/pages/foo"
        assert m.group(2) is None

    def test_aliased_link(self):
        m = WIKILINK_RE.search("See [[wiki/pages/foo|Foo Page]].")
        assert m is not None
        assert m.group(1) == "wiki/pages/foo"
        assert m.group(2) == "Foo Page"

    def test_no_match_on_plain_text(self):
        assert WIKILINK_RE.search("no brackets here") is None

    def test_dot_in_slug(self):
        m = WIKILINK_RE.search("[[wiki/sources/arxiv-2602.20867]]")
        assert m is not None
        assert m.group(1) == "wiki/sources/arxiv-2602.20867"


class TestNormalizeLinkTarget:
    def test_vault_relative_with_md(self, tmp_path):
        page = tmp_path / "wiki" / "pages" / "foo.md"
        page.parent.mkdir(parents=True)
        page.write_text("content")
        source = tmp_path / "wiki" / "pages" / "bar.md"
        result = normalize_link_target("wiki/pages/foo.md", tmp_path, source)
        assert result == page

    def test_vault_relative_without_md(self, tmp_path):
        page = tmp_path / "wiki" / "pages" / "foo.md"
        page.parent.mkdir(parents=True)
        page.write_text("content")
        source = tmp_path / "wiki" / "pages" / "bar.md"
        result = normalize_link_target("wiki/pages/foo", tmp_path, source)
        assert result == page

    def test_dot_slug_no_false_extension(self, tmp_path):
        # arxiv-2602.20867 has a dot but is NOT an extension — should find .md
        page = tmp_path / "wiki" / "sources" / "arxiv-2602.20867.md"
        page.parent.mkdir(parents=True)
        page.write_text("content")
        source = tmp_path / "wiki" / "pages" / "bar.md"
        result = normalize_link_target("wiki/sources/arxiv-2602.20867", tmp_path, source)
        assert result == page

    def test_empty_target_returns_none(self, tmp_path):
        source = tmp_path / "wiki" / "pages" / "bar.md"
        assert normalize_link_target("", tmp_path, source) is None

    def test_whitespace_stripped(self, tmp_path):
        page = tmp_path / "wiki" / "pages" / "foo.md"
        page.parent.mkdir(parents=True)
        page.write_text("content")
        source = tmp_path / "wiki" / "pages" / "bar.md"
        result = normalize_link_target("  wiki/pages/foo  ", tmp_path, source)
        assert result == page
