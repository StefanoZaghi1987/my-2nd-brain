"""Tests for init_vault.py deployment correctness."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import init_vault


class TestCommands:
    def test_split_in_commands(self):
        """Every advertised slash command must be in the COMMANDS list."""
        assert "split" in init_vault.COMMANDS

    def test_split_md_exists(self):
        repo = Path(__file__).parent.parent
        assert (repo / "commands" / "split.md").exists()

    # test_retry_* tests are added in Task 7 after commands/retry.md exists.
