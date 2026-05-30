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
        """The commands/split.md source file must exist so init_vault can install it."""
        repo = Path(__file__).parent.parent
        assert (repo / "commands" / "split.md").exists()

    def test_retry_in_commands(self):
        """retry must be in the COMMANDS list now that commands/retry.md exists."""
        assert "retry" in init_vault.COMMANDS

    def test_retry_md_exists(self):
        """The commands/retry.md source file must exist so init_vault can install it."""
        repo = Path(__file__).parent.parent
        assert (repo / "commands" / "retry.md").exists()


class TestAutoDiscover:
    """Tests for script auto-discovery in install_skills."""

    def _minimal_bundle(self, tmp_path, extra_scripts=None, excluded_scripts=None):
        """Create a minimal bundle with all hardcoded scripts plus extras."""
        bundle = tmp_path / "bundle"

        # inbox-fetcher scripts
        inbox_scripts = bundle / "skills" / "inbox-fetcher" / "scripts"
        inbox_scripts.mkdir(parents=True)
        (bundle / "skills" / "inbox-fetcher" / "SKILL.md").write_text("# Skill\npackages: []")
        (inbox_scripts / "fetch_inbox.py").write_text("# fetch")
        (inbox_scripts / "adopt_drop.py").write_text("# adopt")

        # vault-linter scripts
        linter_scripts = bundle / "skills" / "vault-linter" / "scripts"
        linter_scripts.mkdir(parents=True)
        (bundle / "skills" / "vault-linter" / "SKILL.md").write_text("# Skill\npackages: []")
        (linter_scripts / "lint.py").write_text("# lint")

        # view-builder (no scripts)
        (bundle / "skills" / "view-builder").mkdir(parents=True)
        (bundle / "skills" / "view-builder" / "SKILL.md").write_text("# Skill\npackages: []")

        # shared scripts
        shared = bundle / "skills" / "shared"
        shared.mkdir(parents=True)
        for fname in ["vault_state.py", "yamlmini.py", "console.py", "review_scope.py",
                      "find_backlinks.py", "linkutil.py"]:
            (shared / fname).write_text(f"# {fname}")

        # Add any extra scripts to inbox-fetcher
        for name in (extra_scripts or []):
            (inbox_scripts / name).write_text(f"# {name}")

        # Add any excluded scripts (these are created but should not be installed)
        for name in (excluded_scripts or []):
            (inbox_scripts / name).write_text(f"# {name}")

        return bundle

    def _minimal_target(self, tmp_path):
        """Create a minimal target vault with required .claude/ dirs."""
        target = tmp_path / "vault"
        for d in [
            ".claude/skills/inbox-fetcher/scripts",
            ".claude/skills/vault-linter/scripts",
            ".claude/skills/view-builder/templates",
            ".claude/skills/shared",
        ]:
            (target / d).mkdir(parents=True)
        return target

    def test_auto_discovers_new_script(self, tmp_path):
        """A new .py file in scripts/ is installed even if not in any hardcoded list."""
        bundle = self._minimal_bundle(tmp_path, extra_scripts=["_probe.py"])
        target = self._minimal_target(tmp_path)

        init_vault.install_skills(target, bundle)

        installed = target / ".claude" / "skills" / "inbox-fetcher" / "scripts" / "_probe.py"
        assert installed.exists(), "_probe.py was not installed"

    def test_original_scripts_still_installed(self, tmp_path):
        """Existing scripts are still installed after switching to auto-discovery."""
        bundle = self._minimal_bundle(tmp_path)
        target = self._minimal_target(tmp_path)

        init_vault.install_skills(target, bundle)

        assert (target / ".claude" / "skills" / "inbox-fetcher" / "scripts" / "fetch_inbox.py").exists()

    def test_test_files_excluded(self, tmp_path):
        """test_*.py files are NOT installed."""
        bundle = self._minimal_bundle(tmp_path, excluded_scripts=["test_probe.py"])
        target = self._minimal_target(tmp_path)

        init_vault.install_skills(target, bundle)

        excluded = target / ".claude" / "skills" / "inbox-fetcher" / "scripts" / "test_probe.py"
        assert not excluded.exists(), "test_probe.py was incorrectly installed"
