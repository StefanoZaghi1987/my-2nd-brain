import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "inbox-fetcher" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))

from fetch_inbox import find_unchecked_entries, update_inbox, FetchResult, InboxEntry


class TestFindUncheckedEntries:
    def test_finds_simple_unchecked_url(self):
        text = "## To process\n- [ ] https://example.com/article\n"
        entries = find_unchecked_entries(text)
        assert len(entries) == 1
        assert entries[0].url == "https://example.com/article"

    def test_ignores_checked_urls(self):
        text = "- [x] https://example.com/done\n- [ ] https://example.com/todo\n"
        entries = find_unchecked_entries(text)
        assert len(entries) == 1
        assert entries[0].url == "https://example.com/todo"

    def test_parses_tags_sub_bullet(self):
        text = "- [ ] https://example.com/article\n  - tags: ai, reasoning\n"
        entries = find_unchecked_entries(text)
        assert entries[0].tags == ["ai", "reasoning"]

    def test_parses_note_sub_bullet(self):
        text = "- [ ] https://example.com/article\n  - note: focus on evaluation section\n"
        entries = find_unchecked_entries(text)
        assert entries[0].note == "focus on evaluation section"

    def test_entry_without_sub_bullets_has_defaults(self):
        text = "- [ ] https://example.com/article\n"
        entries = find_unchecked_entries(text)
        assert entries[0].tags == []
        assert entries[0].note is None

    def test_both_tags_and_note_on_same_entry(self):
        text = (
            "- [ ] https://example.com/article\n"
            "  - tags: llm, agents\n"
            "  - note: read section 3 carefully\n"
        )
        entries = find_unchecked_entries(text)
        assert entries[0].tags == ["llm", "agents"]
        assert entries[0].note == "read section 3 carefully"

    def test_strips_urls_inside_html_comments(self):
        text = "<!-- - [ ] https://example.com/comment -->\n- [ ] https://example.com/real\n"
        entries = find_unchecked_entries(text)
        assert len(entries) == 1
        assert entries[0].url == "https://example.com/real"

    def test_tags_stripped_of_whitespace(self):
        text = "- [ ] https://example.com/a\n  - tags:  ai ,  llm \n"
        entries = find_unchecked_entries(text)
        assert entries[0].tags == ["ai", "llm"]


class TestUpdateInbox:
    def test_successful_result_moves_to_processed_section(self):
        inbox = "## To process\n- [ ] https://example.com/article\n"
        results = [FetchResult(
            url="https://example.com/article", ok=True, kind="html",
            out_path=Path("raw/web/article-slug/"),
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "- [x] https://example.com/article" in new_text
        assert "## Processed" in new_text

    def test_failed_result_stays_unchecked_with_reason(self):
        inbox = "## To process\n- [ ] https://paywall.com/article\n"
        results = [FetchResult(
            url="https://paywall.com/article", ok=False, kind="failed",
            reason="extraction empty — try playwright",
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "- [ ] https://paywall.com/article ⚠" in new_text

    def test_uses_config_section_name(self):
        inbox = "## To process\n- [ ] https://example.com/a\n"
        results = [FetchResult(
            url="https://example.com/a", ok=True, kind="html",
            out_path=Path("raw/web/a/"),
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Done")
        assert "## Done" in new_text
        assert "## Processed" not in new_text
