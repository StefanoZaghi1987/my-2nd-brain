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
        assert "." not in slug

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
