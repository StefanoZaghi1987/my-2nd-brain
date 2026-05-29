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


class TestCheckConversations:
    def test_no_findings_for_absent_conversations_dir(self, tmp_path):
        from lint import check_conversations
        assert check_conversations(tmp_path) == []

    def test_no_findings_when_type_present(self, tmp_path):
        conv = tmp_path / "conversations"
        conv.mkdir()
        (conv / "2026-05-01-session.md").write_text(
            "---\ntype: conversation\ndate: 2026-05-01\n---\n## Question\nWhat?\n"
        )
        from lint import check_conversations
        assert check_conversations(tmp_path) == []

    def test_advisory_for_missing_type_field(self, tmp_path):
        conv = tmp_path / "conversations"
        conv.mkdir()
        (conv / "2026-05-01-session.md").write_text(
            "---\ndate: 2026-05-01\n---\n## Question\nWhat?\n"
        )
        from lint import check_conversations
        findings = check_conversations(tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "missing_conversation_type"
        assert findings[0].severity == "advisory"


class TestCheckIndexSync:
    def test_no_findings_when_index_absent(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/sources/agent-skills.md": (
                "---\ntype: source\nsource_path: raw/web/agent-skills/index.md\n"
                "created: 2026-01-01\nupdated: 2026-01-01\n---\n# Agent Skills\n"
            ),
        })
        from lint import load_wiki, check_index_sync
        pages = load_wiki(tmp_path)
        assert check_index_sync(pages, tmp_path) == []

    def test_no_findings_when_source_listed_in_index(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/sources/agent-skills.md": (
                "---\ntype: source\nsource_path: raw/web/agent-skills/index.md\n"
                "created: 2026-01-01\nupdated: 2026-01-01\n---\n# Agent Skills\n"
            ),
            "wiki/index.md": "# Index\n\n- [[wiki/sources/agent-skills]]\n",
        })
        from lint import load_wiki, check_index_sync
        pages = load_wiki(tmp_path)
        assert check_index_sync(pages, tmp_path) == []

    def test_advisory_when_source_absent_from_index(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/sources/agent-skills.md": (
                "---\ntype: source\nsource_path: raw/web/agent-skills/index.md\n"
                "created: 2026-01-01\nupdated: 2026-01-01\n---\n# Agent Skills\n"
            ),
            "wiki/index.md": "# Index\n\n## Sources\n\n<!-- empty -->\n",
        })
        from lint import load_wiki, check_index_sync
        pages = load_wiki(tmp_path)
        findings = check_index_sync(pages, tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "index_sync"
        assert findings[0].severity == "advisory"
        assert "agent-skills" in findings[0].file


class TestCheckLocalIndex:
    def test_no_findings_when_local_dir_absent(self, tmp_path):
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_advisory_for_local_subdir_without_index(self, tmp_path):
        slug = tmp_path / "raw" / "local" / "my-paper"
        slug.mkdir(parents=True)
        (slug / "paper.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        assert any(f.check == "missing_pdf_index" for f in findings)
        assert all(f.severity == "advisory" for f in findings)
        finding = next(f for f in findings if f.check == "missing_pdf_index")
        assert "raw/local/" in finding.detail

    def test_no_findings_for_correct_local_structure(self, tmp_path):
        slug = tmp_path / "raw" / "local" / "my-paper"
        slug.mkdir(parents=True)
        (slug / "paper.pdf").write_bytes(b"%PDF")
        (slug / "index.md").write_text("---\nfetch_method: local-pdf\n---\n")
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_advisory_for_flat_pdf_in_local(self, tmp_path):
        local = tmp_path / "raw" / "local"
        local.mkdir(parents=True)
        (local / "orphan.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        assert any(f.check == "legacy_flat_pdf" for f in findings)

    def test_checks_both_papers_and_local(self, tmp_path):
        (tmp_path / "raw" / "papers" / "p1").mkdir(parents=True)
        (tmp_path / "raw" / "papers" / "p1" / "paper.pdf").write_bytes(b"%PDF")
        (tmp_path / "raw" / "local" / "p2").mkdir(parents=True)
        (tmp_path / "raw" / "local" / "p2" / "paper.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        files = [f.file for f in findings]
        assert any("papers" in fp for fp in files)


class TestCheckDropZone:
    def test_no_findings_when_drop_zone_absent(self, tmp_path):
        from lint import check_drop_zone
        assert check_drop_zone(tmp_path) == []

    def test_no_findings_when_drop_zone_empty(self, tmp_path):
        (tmp_path / "raw" / "drop").mkdir(parents=True)
        from lint import check_drop_zone
        assert check_drop_zone(tmp_path) == []

    def test_advisory_when_pdf_present(self, tmp_path):
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "unprocessed.pdf").write_bytes(b"%PDF")
        from lint import check_drop_zone
        findings = check_drop_zone(tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "drop_zone_not_empty"
        assert findings[0].severity == "advisory"

    def test_detail_mentions_count(self, tmp_path):
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "a.pdf").write_bytes(b"%PDF")
        (drop / "b.pdf").write_bytes(b"%PDF")
        from lint import check_drop_zone
        findings = check_drop_zone(tmp_path)
        assert "2" in findings[0].detail

    def test_ignores_non_pdf_files(self, tmp_path):
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "notes.txt").write_text("just a note")
        from lint import check_drop_zone
        assert check_drop_zone(tmp_path) == []

    def test_no_findings_when_drop_zone_disabled(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "drop_zone:\n  enabled: false\n  path: raw/drop\n"
        )
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper.pdf").write_bytes(b"%PDF")
        from lint import check_drop_zone
        assert check_drop_zone(tmp_path) == []

    def test_detects_md_files_in_drop_zone(self, tmp_path):
        from lint import check_drop_zone
        (tmp_path / "vault.config.yml").write_text(
            "drop_zone:\n  enabled: true\n  path: raw/drop\n"
        )
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "my-note.md").write_text("# My Note\ncontent")

        findings = check_drop_zone(tmp_path)

        assert len(findings) == 1
        assert findings[0].check == "drop_zone_not_empty"
        assert "Markdown" in findings[0].detail

    def test_reports_mixed_types_pdf_first(self, tmp_path):
        from lint import check_drop_zone
        (tmp_path / "vault.config.yml").write_text(
            "drop_zone:\n  enabled: true\n  path: raw/drop\n"
        )
        drop = tmp_path / "raw" / "drop"
        drop.mkdir(parents=True)
        (drop / "paper.pdf").write_bytes(b"%PDF")
        (drop / "note.md").write_text("# Note\n")

        findings = check_drop_zone(tmp_path)

        assert len(findings) == 1
        assert "PDF" in findings[0].detail
        assert "Markdown" in findings[0].detail
        assert findings[0].detail.index("PDF") < findings[0].detail.index("Markdown")


class TestLintGracefulDegradation:
    def test_crashing_check_produces_advisory_not_exit_2(self, tmp_path):
        """A check that raises must produce an advisory, not abort the whole run."""
        import unittest.mock as mock
        import lint as lint_mod
        from lint import run_lint

        # Minimal valid vault with wiki/ structure
        (tmp_path / "wiki" / "pages").mkdir(parents=True)
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / ".lint").mkdir(parents=True)

        with mock.patch.object(lint_mod, "check_gaps",
                               side_effect=RuntimeError("intentional test crash")):
            exit_code = run_lint(tmp_path, quiet=True)

        # Must exit 1 (findings), not 2 (catastrophic abort)
        assert exit_code == 1

        # The report must mention the crash
        report = (tmp_path / ".lint" / "report.md").read_text()
        assert "check_gaps" in report or "intentional test crash" in report
