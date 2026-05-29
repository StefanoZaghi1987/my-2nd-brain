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


class TestAdoptPdf:
    def test_moves_pdf_and_creates_index(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "attention-is-all-you-need.pdf").write_bytes(b"%PDF-1.4 fake")
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)

        result = adopt_pdf(drop / "attention-is-all-you-need.pdf", local)

        assert result.ok
        assert result.slug == "attention-is-all-you-need"
        assert not (drop / "attention-is-all-you-need.pdf").exists()
        assert (local / "attention-is-all-you-need" / "paper.pdf").exists()
        index = (local / "attention-is-all-you-need" / "index.md").read_text()
        assert "fetch_method: local-pdf" in index
        assert "Attention Is All You Need" in index
        assert "source_url" not in index

    def test_index_has_required_frontmatter(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "lecun-path.pdf").write_bytes(b"%PDF")
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)

        adopt_pdf(drop / "lecun-path.pdf", local)

        index = (local / "lecun-path" / "index.md").read_text()
        assert "fetch_method: local-pdf" in index
        assert "title:" in index
        assert "fetched:" in index
        assert "tags: []" in index
        assert "PDF: [[paper.pdf]]" in index

    def test_skips_on_slug_collision(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "my-paper.pdf").write_bytes(b"%PDF")
        local = tmp_path / "raw" / "local"
        (local / "my-paper").mkdir(parents=True)
        (local / "my-paper" / "paper.pdf").write_bytes(b"%PDF existing")

        result = adopt_pdf(drop / "my-paper.pdf", local)

        assert not result.ok
        assert "already exists" in result.reason
        assert (drop / "my-paper.pdf").exists()  # not moved

    def test_dry_run_does_not_move_file(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "my-paper.pdf").write_bytes(b"%PDF")
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)

        result = adopt_pdf(drop / "my-paper.pdf", local, dry_run=True)

        assert result.ok
        assert (drop / "my-paper.pdf").exists()  # not moved
        assert not (local / "my-paper").exists()  # not created

    def test_empty_slug_returns_failed_result(self, tmp_path):
        from adopt_drop import adopt_pdf
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        # "----.pdf" slugifies to "" via python-slugify
        (drop / "----.pdf").write_bytes(b"%PDF")
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)

        result = adopt_pdf(drop / "----.pdf", local)

        assert not result.ok
        assert result.slug == ""
        assert (drop / "----.pdf").exists()  # not moved

    def test_rollback_on_index_write_failure(self, tmp_path, monkeypatch):
        from adopt_drop import adopt_pdf
        from pathlib import Path

        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "my-paper.pdf").write_bytes(b"%PDF")
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)

        # Simulate write_text raising an OSError after PDF has been moved
        original_write_text = Path.write_text

        def failing_write_text(self, *args, **kwargs):
            if self.name == "index.md":
                raise OSError("simulated disk full")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", failing_write_text)

        with pytest.raises(OSError, match="simulated disk full"):
            adopt_pdf(drop / "my-paper.pdf", local)

        # PDF must be restored to drop zone
        assert (drop / "my-paper.pdf").exists()
        # Partial directory must be fully cleaned up
        assert not (local / "my-paper").exists()


class TestProcessDropZone:
    def test_ignores_non_pdf_files(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "notes.docx").write_bytes(b"fake docx")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 0
        assert (drop / "notes.docx").exists()
        assert not list((tmp_path / "raw" / "local").iterdir())

    def test_adopts_multiple_pdfs(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper-one.pdf").write_bytes(b"%PDF")
        (drop / "paper-two.pdf").write_bytes(b"%PDF")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 0
        assert (tmp_path / "raw" / "local" / "paper-one" / "paper.pdf").exists()
        assert (tmp_path / "raw" / "local" / "paper-two" / "paper.pdf").exists()

    def test_returns_exit_code_2_when_some_skipped(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "collision.pdf").write_bytes(b"%PDF new")
        local = tmp_path / "raw" / "local"
        (local / "collision").mkdir(parents=True)
        (local / "collision" / "paper.pdf").write_bytes(b"%PDF existing")

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 2

    def test_skips_when_drop_zone_disabled(self, tmp_path):
        from adopt_drop import process_drop_zone
        (tmp_path / "vault.config.yml").write_text(
            "drop_zone:\n  enabled: false\n  path: raw/drop\n"
        )
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper.pdf").write_bytes(b"%PDF")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        exit_code = process_drop_zone(tmp_path)

        assert exit_code == 0
        assert (drop / "paper.pdf").exists()  # not moved

    def test_returns_0_when_drop_zone_absent(self, tmp_path):
        from adopt_drop import process_drop_zone
        exit_code = process_drop_zone(tmp_path)
        assert exit_code == 0

    def test_dry_run_does_not_move_any_file(self, tmp_path):
        from adopt_drop import process_drop_zone
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper.pdf").write_bytes(b"%PDF")
        (tmp_path / "raw" / "local").mkdir(parents=True)

        process_drop_zone(tmp_path, dry_run=True)

        assert (drop / "paper.pdf").exists()


class TestExtractTitleFromMd:
    def test_returns_frontmatter_title(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text('---\ntitle: "My Obsidian Note"\n---\n# Different Heading\nsome body')
        assert extract_title_from_md(f) == "My Obsidian Note"

    def test_frontmatter_title_without_quotes(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("---\ntitle: Plain Title\n---\nsome body")
        assert extract_title_from_md(f) == "Plain Title"

    def test_falls_back_to_h1_when_no_frontmatter_title(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("---\nauthor: Alice\n---\n# My Heading\nsome body")
        assert extract_title_from_md(f) == "My Heading"

    def test_falls_back_to_h1_when_no_frontmatter(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("# My Heading\nsome body")
        assert extract_title_from_md(f) == "My Heading"

    def test_returns_none_when_nothing_found(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("just some prose with no heading")
        assert extract_title_from_md(f) is None

    def test_handles_empty_frontmatter(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("---\n---\n# Heading After Empty\n")
        assert extract_title_from_md(f) == "Heading After Empty"

    def test_handles_malformed_frontmatter_no_closing(self, tmp_path):
        from adopt_drop import extract_title_from_md
        f = tmp_path / "note.md"
        f.write_text("---\ntitle: orphan\n# Heading\n")
        # No closing ---, frontmatter regex won't match; falls to H1
        assert extract_title_from_md(f) == "Heading"


class TestExtractSourceUrlFromMd:
    def test_reads_source_url_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "clip.md"
        f.write_text("---\nsource_url: https://example.com/article\n---\nbody")
        assert extract_source_url_from_md(f) == "https://example.com/article"

    def test_reads_url_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "clip.md"
        f.write_text("---\nurl: https://example.com\n---\nbody")
        assert extract_source_url_from_md(f) == "https://example.com"

    def test_reads_link_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "clip.md"
        f.write_text("---\nlink: https://example.com\n---\nbody")
        assert extract_source_url_from_md(f) == "https://example.com"

    def test_reads_source_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "clip.md"
        f.write_text("---\nsource: https://example.com\n---\nbody")
        assert extract_source_url_from_md(f) == "https://example.com"

    def test_returns_none_when_no_known_key(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "note.md"
        f.write_text("---\ntitle: My Note\nauthor: Alice\n---\nbody")
        assert extract_source_url_from_md(f) is None

    def test_returns_none_when_no_frontmatter(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "note.md"
        f.write_text("# Just a heading\nno frontmatter here")
        assert extract_source_url_from_md(f) is None

    def test_handles_empty_frontmatter(self, tmp_path):
        from adopt_drop import extract_source_url_from_md
        f = tmp_path / "note.md"
        f.write_text("---\n---\nbody")
        assert extract_source_url_from_md(f) is None
