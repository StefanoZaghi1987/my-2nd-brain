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


class TestFetchHtmlFrontmatter:
    def test_tags_and_note_appear_in_raw_index_md(self, tmp_path):
        import unittest.mock
        fake_html = "<html><body><h1>Test Article</h1><p>content</p></body></html>"
        canned_md = "# Test Article\n\ncontent\n"
        with (
            unittest.mock.patch("trafilatura.fetch_url", return_value=fake_html),
            unittest.mock.patch("trafilatura.extract", return_value=canned_md),
            unittest.mock.patch("trafilatura.extract_metadata", return_value=None),
        ):
            from fetch_inbox import fetch_html
            result = fetch_html(
                "https://example.com/article",
                tmp_path / "raw" / "web",
                tags=["ai", "llm"],
                note='focus on "section 3"',
            )
        assert result.ok
        index_text = (result.out_path / "index.md").read_text()
        assert "tags: [ai, llm]" in index_text
        assert "section 3" in index_text


class TestFetchPdfStructure:
    def test_creates_folder_with_pdf_and_index(self, tmp_path, requests_mock):
        from fetch_inbox import fetch_pdf
        papers_dir = tmp_path / "raw" / "papers"
        papers_dir.mkdir(parents=True)
        requests_mock.get("https://arxiv.org/pdf/2405.12345.pdf",
                          content=b"%PDF-1.4 fake")
        result = fetch_pdf(
            "https://arxiv.org/pdf/2405.12345.pdf",
            papers_dir,
            slug_override="arxiv-2405-12345",
            tags=["llm"],
            note="read section 3",
        )
        assert result.ok
        assert (result.out_path / "paper.pdf").exists()
        assert (result.out_path / "index.md").exists()
        index_text = (result.out_path / "index.md").read_text()
        assert "fetch_method: pdf" in index_text
        assert "tags: [llm]" in index_text
        assert "read section 3" in index_text


class TestUpdateInboxSubBullets:
    def test_successful_url_drops_sub_bullets(self):
        inbox = (
            "## To process\n"
            "- [ ] https://example.com/article\n"
            "  - tags: ai, llm\n"
            "  - note: read carefully\n"
        )
        results = [FetchResult(
            url="https://example.com/article", ok=True, kind="html",
            out_path=Path("raw/web/article/"),
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "tags: ai" not in new_text
        assert "note: read" not in new_text
        assert "- [x] https://example.com/article" in new_text

    def test_failed_url_keeps_sub_bullets(self):
        inbox = (
            "## To process\n"
            "- [ ] https://paywall.com/article\n"
            "  - tags: ai\n"
            "  - note: important section\n"
        )
        results = [FetchResult(
            url="https://paywall.com/article", ok=False, kind="failed",
            reason="extraction empty — try playwright",
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "- [ ] https://paywall.com/article ⚠" in new_text
        assert "tags: ai" in new_text
        assert "note: important section" in new_text

    def test_unprocessed_url_keeps_sub_bullets(self):
        inbox = (
            "## To process\n"
            "- [ ] https://example.com/other\n"
            "  - tags: other\n"
        )
        new_text = update_inbox(Path("dummy"), inbox, [],
                                processed_section="## Processed")
        assert "- [ ] https://example.com/other" in new_text
        assert "tags: other" in new_text


class TestPdfEnabled:
    def test_pdf_url_skipped_when_disabled(self, tmp_path, requests_mock):
        from fetch_inbox import process_vault
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  pdf_enabled: false\n"
        )
        (tmp_path / "inbox.md").write_text(
            "- [ ] https://arxiv.org/pdf/2405.12345.pdf\n"
        )
        (tmp_path / "raw" / "papers").mkdir(parents=True)
        (tmp_path / "raw" / "web").mkdir(parents=True)
        # Safety net: if fetch_pdf is incorrectly called, this 403 makes it fail loudly
        requests_mock.get(
            "https://arxiv.org/pdf/2405.12345.pdf",
            status_code=403,
        )
        process_vault(tmp_path)
        inbox_text = (tmp_path / "inbox.md").read_text()
        # Check that the URL was marked as failed with pdf_enabled message
        assert "- [ ]" in inbox_text  # Still unchecked
        assert "pdf_enabled" in inbox_text  # Contains our error message
        # Verify no PDF file was actually downloaded
        assert not any(
            entry.is_file()
            for entry in (tmp_path / "raw" / "papers").rglob("*")
        )
