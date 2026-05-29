"""
Characterization tests for yamlmini.parse_yaml / parse_frontmatter.

Section A: Reproduce vault_state._parse_config_yaml behaviour exactly.
Section B: Reproduce lint.parse_frontmatter behaviour exactly.
Section C: New capability — block lists under a config section (the headline fix).
Section D: Differential parity — verify yamlmini matches BOTH old parsers exactly
           over their existing test fixtures. Run BEFORE deleting old parsers.
           Remove Section D once Tasks 2-3 delete the old functions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "vault-linter" / "scripts"))
from yamlmini import parse_yaml, parse_frontmatter


# ── Section A: vault_state._parse_config_yaml characterisation ──────────────

class TestParseYamlConfig:
    """Mirrors the exact cases from test_vault_state.py::TestLoadConfig."""

    def test_scalar_int(self):
        assert parse_yaml("fetch:\n  html_timeout_seconds: 45\n") == {
            "fetch": {"html_timeout_seconds": 45}
        }

    def test_scalar_bool_false(self):
        assert parse_yaml("fetch:\n  pdf_enabled: false\n") == {
            "fetch": {"pdf_enabled": False}
        }

    def test_scalar_bool_true(self):
        assert parse_yaml("fetch:\n  pdf_enabled: true\n") == {
            "fetch": {"pdf_enabled": True}
        }

    def test_inline_list_under_section(self):
        result = parse_yaml("fetch:\n  walled_domains: [example.com, other.com]\n")
        assert result["fetch"]["walled_domains"] == ["example.com", "other.com"]

    def test_inline_comment_stripped(self):
        result = parse_yaml("lint:\n  stale_source_days: 90  # some comment here\n")
        assert result["lint"]["stale_source_days"] == 90

    def test_two_sections_independent(self):
        text = "fetch:\n  html_timeout_seconds: 20\nlint:\n  stale_source_days: 180\n"
        result = parse_yaml(text)
        assert result["fetch"]["html_timeout_seconds"] == 20
        assert result["lint"]["stale_source_days"] == 180

    def test_override_preserves_sibling_keys(self):
        """Partial override: one key overridden, sibling keys NOT in text are absent."""
        result = parse_yaml("lint:\n  stale_source_days: 90\n")
        assert result["lint"]["stale_source_days"] == 90
        assert "view_stale_days" not in result["lint"]

    def test_null_scalar(self):
        result = parse_yaml("state:\n  last_lint: null\n")
        assert result["state"]["last_lint"] is None

    def test_empty_inline_list(self):
        result = parse_yaml("fetch:\n  walled_domains: []\n")
        assert result["fetch"]["walled_domains"] == []


# ── Section B: lint.parse_frontmatter characterisation ──────────────────────

class TestParseFrontmatter:
    """Mirrors the frontmatter shapes used across the vault."""

    def test_returns_empty_when_no_frontmatter(self):
        assert parse_frontmatter("No frontmatter here.\n") == {}

    def test_scalar_fields(self):
        fm = parse_frontmatter("---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-05-29\n---\n")
        assert fm["type"] == "page"
        assert fm["created"] == "2026-01-01"
        assert fm["updated"] == "2026-05-29"

    def test_inline_list_tags(self):
        fm = parse_frontmatter("---\ntags: [ai, ml, nlp]\n---\n")
        assert fm["tags"] == ["ai", "ml", "nlp"]

    def test_empty_inline_list(self):
        fm = parse_frontmatter("---\ntags: []\n---\n")
        assert fm["tags"] == []

    def test_block_list_based_on(self):
        text = (
            "---\n"
            "type: view\n"
            "based_on:\n"
            "  - [[wiki/pages/foo]]\n"
            "  - [[wiki/pages/bar]]\n"
            "---\n"
        )
        fm = parse_frontmatter(text)
        assert fm["based_on"] == ["[[wiki/pages/foo]]", "[[wiki/pages/bar]]"]

    def test_block_list_tags(self):
        text = "---\ntags:\n  - ai\n  - ml\n---\n"
        fm = parse_frontmatter(text)
        assert fm["tags"] == ["ai", "ml"]

    def test_quoted_value_with_colon(self):
        fm = parse_frontmatter('---\ntitle: "Deep Learning: A Primer"\n---\n')
        assert fm["title"] == "Deep Learning: A Primer"

    def test_body_is_not_parsed(self):
        """Frontmatter extraction stops at closing ---; body is ignored."""
        text = "---\ntype: page\n---\n\nupdated: 9999-12-31\n"
        fm = parse_frontmatter(text)
        assert fm["type"] == "page"
        assert "updated" not in fm

    def test_shareable_bool(self):
        fm = parse_frontmatter("---\nshareable: false\n---\n")
        assert fm["shareable"] is False


# ── Section C: New capability — block list under a config section ───────────

class TestBlockListUnderSection:
    """The headline regression guard: walled_domains as block list."""

    def test_block_list_under_section(self):
        text = (
            "fetch:\n"
            "  walled_domains:\n"
            "    - x.com\n"
            "    - twitter.com\n"
            "    - linkedin.com\n"
        )
        result = parse_yaml(text)
        assert result["fetch"]["walled_domains"] == ["x.com", "twitter.com", "linkedin.com"]

    def test_block_list_under_section_with_siblings(self):
        """Block list key coexists with scalar siblings in the same section."""
        text = (
            "fetch:\n"
            "  html_timeout_seconds: 20\n"
            "  walled_domains:\n"
            "    - x.com\n"
            "    - twitter.com\n"
            "  pdf_enabled: true\n"
        )
        result = parse_yaml(text)
        assert result["fetch"]["html_timeout_seconds"] == 20
        assert result["fetch"]["walled_domains"] == ["x.com", "twitter.com"]
        assert result["fetch"]["pdf_enabled"] is True

    def test_inline_and_block_produce_same_value(self):
        """Inline syntax and block syntax produce identical results."""
        inline = parse_yaml("fetch:\n  walled_domains: [x.com, twitter.com]\n")
        block = parse_yaml("fetch:\n  walled_domains:\n    - x.com\n    - twitter.com\n")
        assert inline["fetch"]["walled_domains"] == block["fetch"]["walled_domains"]

    def test_empty_section_header_produces_dict_not_empty_string(self):
        """A top-level key with no sub-keys before the next section must produce {}
        (not ""), matching old _parse_config_yaml. Critical for _deep_merge in load_config:
        _deep_merge checks isinstance(v, dict); "" fails that check and replaces the
        entire defaults dict, causing TypeError on any subsequent key access.
        """
        text = "fetch:\nlint:\n  stale_source_days: 90\n"
        result = parse_yaml(text)
        assert result["fetch"] == {}, (
            "Empty section header must produce {} not '' — '' corrupts _deep_merge"
        )
        assert result["lint"]["stale_source_days"] == 90

    def test_block_list_items_scalar_coercion(self):
        """Block-list items undergo scalar coercion same as inline-list items.
        inline [1, 2] == block - 1 / - 2 for integer values.
        """
        block = parse_yaml("nums:\n  - 1\n  - 2\n")
        inline = parse_yaml("nums: [1, 2]\n")
        assert block["nums"] == [1, 2], "Block-list integers should be coerced to int"
        assert inline["nums"] == block["nums"]


# ── Section D: Differential parity (transient — remove after Tasks 2-3) ─────

class TestDifferentialParity:
    """
    Verify yamlmini produces IDENTICAL output to old parsers over their
    existing fixtures. This is the 'zero behavior change' gate.

    vault_state._parse_config_yaml was deleted in Task 2; parity test removed.
    Remove this class once lint.parse_frontmatter is deleted in Task 3.
    """

    def _get_old_lint_parser(self):
        """Import the old lint.parse_frontmatter (returns (dict, body) tuple).

        lint.py uses dataclasses with forward-reference annotations that require
        the module to be registered in sys.modules before exec_module runs.
        Register it first to avoid AttributeError in dataclasses resolution.
        """
        import importlib.util
        import sys as _sys
        spec = importlib.util.spec_from_file_location(
            "_lint_old",
            Path(__file__).parent.parent / "skills" / "vault-linter" / "scripts" / "lint.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        # Register in sys.modules before exec so dataclass forward refs resolve
        _sys.modules["_lint_old"] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore
        except Exception:
            del _sys.modules["_lint_old"]
            raise
        return mod.parse_frontmatter

    FM_FIXTURES = [
        "No frontmatter here.\n",
        "---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-05-29\n---\n",
        "---\ntags: [ai, ml, nlp]\n---\n",
        "---\ntags: []\n---\n",
        "---\ntype: view\nbased_on:\n  - [[wiki/pages/foo]]\n  - [[wiki/pages/bar]]\n---\n",
        "---\ntags:\n  - ai\n  - ml\n---\n",
        '---\ntitle: "Deep Learning: A Primer"\n---\n',
        "---\ntype: page\n---\n\nupdated: 9999-12-31\n",
        "---\nshareable: false\n---\n",
    ]

    # Fixtures where yamlmini intentionally diverges from old lint.parse_frontmatter:
    # yamlmini coerces scalars (false -> False, true -> True, null -> None, integers),
    # while old lint.parse_frontmatter stored all scalars as raw strings.
    # This is an intentional improvement, not a regression.
    FM_FIXTURES_COERCION_DIVERGENT = {
        "---\nshareable: false\n---\n",  # old: {"shareable": "false"}, new: {"shareable": False}
    }

    def test_frontmatter_dict_parity(self):
        """parse_frontmatter dict matches lint.parse_frontmatter dict on non-coercion fixtures.

        NOTE: Fixtures where yamlmini intentionally coerces scalars (e.g. false->False)
        are excluded — old lint.parse_frontmatter stored scalars as raw strings, while
        yamlmini.parse_frontmatter applies _parse_scalar coercion. This is an intentional
        improvement tested in Section B (test_shareable_bool etc.).
        """
        old_parse = self._get_old_lint_parser()
        for fixture in self.FM_FIXTURES:
            if fixture in self.FM_FIXTURES_COERCION_DIVERGENT:
                continue  # yamlmini intentionally coerces scalars; old parser stored raw strings
            expected_dict, expected_body = old_parse(fixture)
            actual_dict = parse_frontmatter(fixture)
            assert actual_dict == expected_dict, (
                f"Dict parity failure on fixture:\n{fixture!r}\n"
                f"old={expected_dict!r}\nnew={actual_dict!r}"
            )

    def test_frontmatter_body_parity(self):
        """The _parse_frontmatter_with_body adapter body matches old lint.parse_frontmatter body.

        NOTE: Coercion-divergent fixtures are excluded for the same reason as
        test_frontmatter_dict_parity — scalar coercion is an intentional improvement.
        """
        import re as _re
        old_parse = self._get_old_lint_parser()

        def _new_with_body(text: str):
            fm = parse_frontmatter(text)
            m = _re.match(r"^---\n.*?\n---\n?", text, _re.DOTALL)
            body = text[m.end():].lstrip("\n") if m else text
            return fm, body

        for fixture in self.FM_FIXTURES:
            if fixture in self.FM_FIXTURES_COERCION_DIVERGENT:
                continue  # yamlmini intentionally coerces scalars; old parser stored raw strings
            expected = old_parse(fixture)
            actual = _new_with_body(fixture)
            assert actual == expected, (
                f"Body parity failure on fixture:\n{fixture!r}\n"
                f"old={expected!r}\nnew={actual!r}"
            )
