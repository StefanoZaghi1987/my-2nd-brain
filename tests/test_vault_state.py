import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from vault_state import load_config, read_state, write_state


class TestReadState:
    def test_returns_empty_dict_when_absent(self, tmp_path):
        assert read_state(tmp_path) == {}

    def test_parses_existing_state_file(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text(
            "last_lint: 2026-01-01\nfetches_since_last_lint: 3\n"
        )
        state = read_state(tmp_path)
        assert state["last_lint"] == "2026-01-01"
        assert state["fetches_since_last_lint"] == "3"

    def test_ignores_comment_lines(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text(
            "# comment\nlast_lint: 2026-01-01\n"
        )
        state = read_state(tmp_path)
        assert "# comment" not in state
        assert state["last_lint"] == "2026-01-01"


class TestWriteState:
    def test_creates_file_and_lint_dir_when_absent(self, tmp_path):
        write_state(tmp_path, {"fetches_since_last_lint": 1})
        assert (tmp_path / ".lint" / "state.yaml").exists()

    def test_patches_existing_key(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text(
            "last_lint: 2026-01-01\nfetches_since_last_lint: 3\n"
        )
        write_state(tmp_path, {"fetches_since_last_lint": 5})
        assert read_state(tmp_path)["fetches_since_last_lint"] == "5"

    def test_preserves_keys_not_in_updates(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text(
            "last_lint: 2026-01-01\nfetches_since_last_lint: 3\n"
        )
        write_state(tmp_path, {"fetches_since_last_lint": 5})
        assert read_state(tmp_path)["last_lint"] == "2026-01-01"

    def test_adds_new_key_to_existing_file(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text("last_lint: 2026-01-01\n")
        write_state(tmp_path, {"fetches_since_last_lint": 1})
        state = read_state(tmp_path)
        assert state["fetches_since_last_lint"] == "1"
        assert state["last_lint"] == "2026-01-01"


class TestLoadConfig:
    def test_returns_all_default_sections_when_absent(self, tmp_path):
        config = load_config(tmp_path)
        assert config["inbox"]["processed_section"] == "## Processed"
        assert config["lint"]["stale_source_days"] == 180
        assert config["fetch"]["html_timeout_seconds"] == 20
        assert isinstance(config["fetch"]["walled_domains"], list)
        assert "x.com" in config["fetch"]["walled_domains"]
        assert config["lint"]["reflect_reminder_days"] == 14

    def test_overrides_specific_value_while_preserving_defaults(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "lint:\n  stale_source_days: 90\n"
        )
        config = load_config(tmp_path)
        assert config["lint"]["stale_source_days"] == 90
        assert config["lint"]["view_stale_days"] == 30  # default preserved

    def test_parses_inline_list(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  walled_domains: [example.com, other.com]\n"
        )
        config = load_config(tmp_path)
        assert config["fetch"]["walled_domains"] == ["example.com", "other.com"]

    def test_raises_valueerror_on_unreadable_file(self, tmp_path):
        (tmp_path / "vault.config.yml").write_bytes(b"\xff\xfe\x00\x01invalid")
        with pytest.raises((ValueError, UnicodeDecodeError)):
            load_config(tmp_path)

    def test_parses_boolean_values(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  pdf_enabled: false\n"
        )
        config = load_config(tmp_path)
        assert config["fetch"]["pdf_enabled"] is False

    def test_parses_integer_values(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  html_timeout_seconds: 45\n"
        )
        config = load_config(tmp_path)
        assert config["fetch"]["html_timeout_seconds"] == 45

    def test_ignores_inline_comments(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "lint:\n  stale_source_days: 90  # some comment here\n"
        )
        config = load_config(tmp_path)
        assert config["lint"]["stale_source_days"] == 90
