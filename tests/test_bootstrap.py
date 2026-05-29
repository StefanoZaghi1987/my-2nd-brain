"""Tests for init_vault.py non-interactive bootstrap."""
import sys
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent


class TestNonInteractiveBootstrap:
    def test_yes_flag_completes_without_stdin(self, tmp_path):
        """--yes must bootstrap a vault without reading from stdin."""
        vault = tmp_path / "test-vault"
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "init_vault.py"), str(vault), "--yes"],
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,  # no stdin — hangs if input() called
        )
        assert result.returncode == 0, (
            f"init_vault.py --yes exited {result.returncode}\n"
            f"stdout: {result.stdout[-500:]}\n"
            f"stderr: {result.stderr[-500:]}"
        )

    def test_yes_flag_deploys_commands(self, tmp_path):
        """Commands directory must contain all expected files after --yes bootstrap."""
        vault = tmp_path / "test-vault"
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "init_vault.py"), str(vault), "--yes"],
            capture_output=True, timeout=60, stdin=subprocess.DEVNULL,
        )
        commands_dir = vault / ".claude" / "commands"
        assert (commands_dir / "split.md").exists()
        assert (commands_dir / "fetch.md").exists()
        assert (commands_dir / "lint.md").exists()

    def test_yes_flag_deploys_linkutil(self, tmp_path):
        """linkutil.py must be present in the shared skills directory."""
        vault = tmp_path / "test-vault"
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "init_vault.py"), str(vault), "--yes"],
            capture_output=True, timeout=60, stdin=subprocess.DEVNULL,
        )
        assert (vault / ".claude" / "skills" / "shared" / "linkutil.py").exists()

    def test_yes_flag_deploys_yamlmini_and_console(self, tmp_path):
        """yamlmini.py and console.py must be present after --yes bootstrap.

        These are new shared modules added in Phase 5. If either filename is
        accidentally removed from _SHARED_SCRIPTS in init_vault.py, this test fails.
        """
        vault = tmp_path / "test-vault"
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "init_vault.py"), str(vault), "--yes"],
            capture_output=True, timeout=60, stdin=subprocess.DEVNULL,
        )
        shared = vault / ".claude" / "skills" / "shared"
        assert (shared / "yamlmini.py").exists(), "yamlmini.py missing from installed vault"
        assert (shared / "console.py").exists(), "console.py missing from installed vault"
