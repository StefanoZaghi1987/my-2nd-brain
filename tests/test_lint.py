import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "vault-linter" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))


def make_vault(tmp_path: Path, files: dict) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")
    return tmp_path


class TestStripWikilink:
    def test_strips_double_brackets(self):
        from lint import strip_wikilink
        assert strip_wikilink("[[wiki/pages/foo]]") == "wiki/pages/foo"

    def test_passthrough_when_no_brackets(self):
        from lint import strip_wikilink
        assert strip_wikilink("wiki/pages/foo") == "wiki/pages/foo"

    def test_strips_only_outer_brackets(self):
        from lint import strip_wikilink
        assert strip_wikilink("[[wiki/pages/foo|Label]]") == "wiki/pages/foo|Label"


class TestCheckBasedOnLinks:
    def test_no_findings_when_based_on_resolves(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/pages/topic.md": (
                "---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-01-01\n---\n# Topic\n"
            ),
            "wiki/views/timeline-topic.md": (
                "---\ntype: view\nkind: timeline\ncreated: 2026-01-01\n"
                "updated: 2026-01-01\nshareable: false\nbased_on:\n"
                "  - [[wiki/pages/topic]]\n---\n# Timeline\n"
            ),
        })
        from lint import load_wiki, check_based_on_links
        pages = load_wiki(tmp_path)
        assert check_based_on_links(pages, tmp_path) == []

    def test_blocking_finding_for_missing_based_on_target(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/views/timeline-gone.md": (
                "---\ntype: view\nkind: timeline\ncreated: 2026-01-01\n"
                "updated: 2026-01-01\nshareable: false\nbased_on:\n"
                "  - [[wiki/pages/does-not-exist]]\n---\n# Timeline\n"
            ),
        })
        from lint import load_wiki, check_based_on_links
        pages = load_wiki(tmp_path)
        findings = check_based_on_links(pages, tmp_path)
        assert len(findings) == 1
        assert findings[0].severity == "blocking"
        assert findings[0].check == "based_on_dead_links"

    def test_skips_non_view_pages(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/pages/topic.md": (
                "---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
                "based_on:\n  - [[wiki/pages/ghost]]\n---\n# Topic\n"
            ),
        })
        from lint import load_wiki, check_based_on_links
        pages = load_wiki(tmp_path)
        assert check_based_on_links(pages, tmp_path) == []


class TestCheckPdfIndex:
    def test_no_findings_for_absent_papers_dir(self, tmp_path):
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_no_findings_for_empty_papers_dir(self, tmp_path):
        (tmp_path / "raw" / "papers").mkdir(parents=True)
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_no_findings_for_correct_structure(self, tmp_path):
        slug = tmp_path / "raw" / "papers" / "arxiv-2405-12345"
        slug.mkdir(parents=True)
        (slug / "paper.pdf").write_bytes(b"%PDF")
        (slug / "index.md").write_text("---\nfetch_method: pdf\n---\n")
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_advisory_for_subdir_without_index(self, tmp_path):
        slug = tmp_path / "raw" / "papers" / "arxiv-2405-12345"
        slug.mkdir(parents=True)
        (slug / "paper.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        assert any(f.check == "missing_pdf_index" for f in findings)
        assert all(f.severity == "advisory" for f in findings)

    def test_advisory_for_flat_pdf_file(self, tmp_path):
        papers = tmp_path / "raw" / "papers"
        papers.mkdir(parents=True)
        (papers / "old-paper.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        assert any(f.check == "legacy_flat_pdf" for f in findings)
