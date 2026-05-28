#!/usr/bin/env python3
"""
init_vault.py — Bootstrap a second brain vault (v4).

Usage:
    python3 init_vault.py                     # creates ./second-brain-vault
    python3 init_vault.py /path/to/vault      # explicit path
    python3 init_vault.py --here              # use current directory
    python3 init_vault.py --help

Idempotent: safe to re-run. Asks before overwriting CLAUDE.md.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows (handles ✓, ⚠, ✗ symbols)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, OSError):
        pass


# --- Colors ------------------------------------------------------------------

_ANSI = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _ANSI else text


def info(msg: str) -> None:
    print(_c("34", f"==> {msg}"))


def ok(msg: str) -> None:
    print(_c("32", f"  ✓ {msg}"))


def skip(msg: str) -> None:
    print(_c("2", f"  · {msg}"))


def warn(msg: str) -> None:
    print(_c("33", f"  ⚠ {msg}"))


def err(msg: str) -> None:
    print(_c("31", f"  ✗ {msg}"), file=sys.stderr)


# --- Constants ---------------------------------------------------------------

DIRS = [
    "raw/papers",
    "raw/web",
    "wiki/pages",
    "wiki/sources",
    "wiki/views/assets",
    "conversations",
    ".lint",
    ".claude/skills/inbox-fetcher/scripts",
    ".claude/skills/vault-linter/scripts",
    ".claude/skills/view-builder/templates",
    ".claude/skills/shared",
    ".claude/commands",
    ".obsidian",
]

GITKEEP_DIRS = [
    "raw/papers", "raw/web", "wiki/pages", "wiki/sources",
    "wiki/views", "wiki/views/assets", "conversations", ".lint",
]

COMMANDS = [
    "save", "view", "reflect", "forget", "lint",
    "promote", "refresh", "ingest", "fetch", "hot", "playwright-fetch",
]


def create_dirs(vault: Path) -> None:
    info("Creating folder structure")
    for d in DIRS:
        (vault / d).mkdir(parents=True, exist_ok=True)
    for d in GITKEEP_DIRS:
        gk = vault / d / ".gitkeep"
        if not gk.exists():
            gk.touch()
    ok("directories")


# --- File content constants --------------------------------------------------

_INBOX_MD = """\
# Inbox

URLs to process. The `inbox-fetcher` skill reads this file and pulls
the URLs into `raw/web/`. Check items after fetching.

## To process

<!-- Add URLs here as a task list:
- [ ] https://example.com/article
- [ ] https://arxiv.org/abs/2024.12345
-->

## Processed

<!-- Automatically moved here after fetch. -->
"""

_INDEX_MD = """\
# Index

Catalog of the vault. Updated on every write operation.

## Pages

<!-- Will be populated as you ingest content. -->

## Sources

<!-- One entry per source. -->

## Views

<!-- Timelines, comparisons, slides, etc. -->
"""

_LOG_MD = """\
# Log

Append-only log of vault operations.

Format: `## [YYYY-MM-DD] op | title`
"""

_HOT_MD = """\
## [INIT]

Vault just bootstrapped. No sessions yet.
"""

_LINT_STATE = """\
last_lint: null
fetches_since_last_lint: 0
last_exit_code: null
last_findings_count: 0
"""

_LINT_REPORT = """\
# Lint Report

No lint run yet. Run `python3 .claude/skills/vault-linter/scripts/lint.py`
from the vault root.
"""

_GITIGNORE = """\
# System
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
*.swp

# Python
__pycache__/
*.pyc
.venv/
venv/

# Obsidian workspace (keep vault files, skip user-specific state)
.obsidian/workspace*
.obsidian/cache
"""

_OBSIDIAN_APP_JSON = """\
{
  "useMarkdownLinks": false,
  "newLinkFormat": "relative",
  "readableLineLength": true,
  "attachmentFolderPath": "wiki/views/assets"
}
"""


def _write_if_absent(path: Path, content: str, label: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        ok(label)
    else:
        skip(f"{label} (exists)")


def write_base_files(vault: Path, script_dir: Path) -> None:
    info("Writing base files")

    cfg = vault / "vault.config.yml"
    if not cfg.exists():
        shutil.copy2(script_dir / "vault.config.yml", cfg)
        ok("vault.config.yml")
    else:
        skip("vault.config.yml (exists — keeping user copy)")

    _write_if_absent(vault / "inbox.md", _INBOX_MD, "inbox.md")
    _write_if_absent(vault / "wiki" / "index.md", _INDEX_MD, "wiki/index.md")
    _write_if_absent(vault / "wiki" / "log.md", _LOG_MD, "wiki/log.md")
    _write_if_absent(vault / "wiki" / "hot.md", _HOT_MD, "wiki/hot.md")
    _write_if_absent(vault / ".lint" / "state.yaml", _LINT_STATE, ".lint/state.yaml")
    _write_if_absent(vault / ".lint" / "report.md", _LINT_REPORT, ".lint/report.md")
    _write_if_absent(vault / ".gitignore", _GITIGNORE, ".gitignore")

    obs_cfg = vault / ".obsidian" / "app.json"
    if not obs_cfg.exists():
        obs_cfg.write_text(_OBSIDIAN_APP_JSON, encoding="utf-8")
        ok(".obsidian/app.json")
    else:
        skip(".obsidian/app.json (exists — keeping user config)")


def init_git(vault: Path) -> None:
    info("Git")
    if (vault / ".git").is_dir():
        skip("git repo already exists")
        return
    ans = input("  Initialize a git repo? [Y/n] ").strip().lower()
    if ans in ("n", "no"):
        skip("no git")
        return
    subprocess.run(["git", "init", "-q"], cwd=vault, check=False)
    name = subprocess.run(
        ["git", "config", "--get", "user.name"],
        cwd=vault, capture_output=True, text=True,
    ).stdout.strip()
    email = subprocess.run(
        ["git", "config", "--get", "user.email"],
        cwd=vault, capture_output=True, text=True,
    ).stdout.strip()
    if not name or not email:
        warn("git user identity not configured — skipping initial commit")
        warn("Set with: git config --global user.name 'Your Name'")
        warn("          git config --global user.email 'you@example.com'")
        return
    subprocess.run(["git", "add", "-A"], cwd=vault, check=False)
    subprocess.run(
        ["git", "commit", "-q", "-m", "initial vault bootstrap (v4)"],
        cwd=vault, check=False,
    )
    ok("git initialized")


def check_deps(vault: Path) -> None:
    info("Checking Python dependencies")
    version = subprocess.run(
        [sys.executable, "--version"], capture_output=True, text=True
    )
    ok(f"Python found: {(version.stdout or version.stderr).strip()}")

    all_packages: set[str] = set()
    for skill_md in (vault / ".claude" / "skills").rglob("SKILL.md"):
        for line in skill_md.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("packages:"):
                inner = line.split("[", 1)[-1].rstrip("]")
                for pkg in inner.split(","):
                    pkg = pkg.strip().strip("\"'")
                    if pkg:
                        all_packages.add(pkg)

    _IMPORT_MAP = {"python-slugify": "slugify"}
    missing = []
    for pkg in sorted(all_packages):
        import_name = _IMPORT_MAP.get(pkg, pkg)
        r = subprocess.run(
            [sys.executable, "-c", f"import {import_name}"],
            capture_output=True,
        )
        if r.returncode != 0:
            missing.append(pkg)

    if missing:
        warn(f"missing Python packages: {' '.join(missing)}")
        print(f"      install with: pip install {' '.join(missing)}")
    else:
        ok("all Python dependencies installed")


def install_commands(vault: Path, script_dir: Path) -> None:
    info("Installing slash commands")
    for cmd in COMMANDS:
        src = script_dir / "commands" / f"{cmd}.md"
        dst = vault / ".claude" / "commands" / f"{cmd}.md"
        if src.exists():
            shutil.copy2(src, dst)
            ok(f"command: /{cmd}")
        else:
            warn(f"command {cmd} not found in bundle")


def install_skills(vault: Path, script_dir: Path) -> None:
    info("Installing skills")

    for skill_name, py_scripts in [
        ("inbox-fetcher", ["scripts/fetch_inbox.py"]),
        ("vault-linter", ["scripts/lint.py"]),
        ("view-builder", []),
    ]:
        src_dir = script_dir / "skills" / skill_name
        dst_dir = vault / ".claude" / "skills" / skill_name
        if not src_dir.is_dir():
            warn(f"{skill_name} skill not found in bundle")
            continue
        shutil.copy2(src_dir / "SKILL.md", dst_dir / "SKILL.md")
        for rel in py_scripts:
            dst_py = dst_dir / rel
            shutil.copy2(src_dir / rel, dst_py)
            if os.name != "nt":
                os.chmod(dst_py, 0o755)
        if skill_name == "view-builder":
            templates_src = src_dir / "templates"
            if templates_src.is_dir():
                for f in templates_src.iterdir():
                    if f.is_file():
                        shutil.copy2(f, dst_dir / "templates" / f.name)
        ok(f"skill: {skill_name}")

    shared_src = script_dir / "skills" / "shared" / "vault_state.py"
    if shared_src.exists():
        shutil.copy2(
            shared_src,
            vault / ".claude" / "skills" / "shared" / "vault_state.py",
        )
        ok("shared: vault_state.py")
    else:
        warn("skills/shared not found in bundle")


def install_claude_md(vault: Path, script_dir: Path) -> None:
    info("Installing CLAUDE.md")
    src = script_dir / "CLAUDE.md"
    dst = vault / "CLAUDE.md"

    if dst.exists():
        ans = input("  CLAUDE.md already exists. Overwrite? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            skip("keeping existing CLAUDE.md")
        else:
            shutil.copy2(src, dst)
            ok("CLAUDE.md")
    else:
        shutil.copy2(src, dst)
        ok("CLAUDE.md")

    agents = vault / "AGENTS.md"
    if not agents.exists():
        try:
            os.symlink("CLAUDE.md", str(agents))
            ok("AGENTS.md → CLAUDE.md (symlink)")
        except (OSError, NotImplementedError, PermissionError):
            shutil.copy2(dst, agents)
            ok("AGENTS.md (copy)")


# --- Arg parsing -------------------------------------------------------------

def resolve_vault_dir() -> Path:
    parser = argparse.ArgumentParser(
        prog="init_vault.py",
        description="Bootstrap a second brain vault.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 init_vault.py                  # ./second-brain-vault\n"
            "  python3 init_vault.py ~/knowledge/X    # explicit path\n"
            "  python3 init_vault.py --here           # current directory\n"
        ),
    )
    parser.add_argument(
        "vault_path",
        nargs="?",
        metavar="PATH",
        help="Path to vault root (default: ./second-brain-vault)",
    )
    parser.add_argument(
        "--here",
        action="store_true",
        help="Use the current directory as the vault root",
    )
    args = parser.parse_args()

    if args.here:
        vault_dir = Path.cwd()
    elif args.vault_path:
        vault_dir = Path(args.vault_path)
    else:
        vault_dir = Path("second-brain-vault")

    vault_dir.mkdir(parents=True, exist_ok=True)
    return vault_dir.resolve()


def print_done(vault: Path) -> None:
    py_cmd = "python3" if os.name != "nt" else "python"
    print()
    print(_c("1;32", "Vault ready!"))
    print()
    print(f"  Path: {vault}")
    print()
    print("Next steps:")
    print(f'  1. cd "{vault}"')
    print( "  2. Add URLs to inbox.md (or drop PDFs in raw/papers/)")
    print( "  3. Open Claude Code (or another CLI) in this folder")
    print( "  4. Ask: \"process the inbox\", then \"ingest the new content\"")
    print( "  5. Use /view to build timelines/comparisons/slides")
    print( "  6. Use /save for important conversations")
    print( "  7. Periodically: /reflect → read wiki/compass.md")
    print(f"  (Manual scripts: {py_cmd} .claude/skills/<skill>/scripts/<script>.py)")
    print()


# --- Entry point -------------------------------------------------------------

def main() -> None:
    script_dir = Path(__file__).resolve().parent

    print()
    print(_c("1", "Second Brain Vault — init (v4)"))

    vault = resolve_vault_dir()
    print(_c("2", f"target: {vault}"))
    print()

    create_dirs(vault)
    install_claude_md(vault, script_dir)
    write_base_files(vault, script_dir)
    install_skills(vault, script_dir)
    install_commands(vault, script_dir)
    init_git(vault)
    check_deps(vault)
    print_done(vault)


if __name__ == "__main__":
    main()
