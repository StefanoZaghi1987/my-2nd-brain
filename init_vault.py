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


# --- Entry point (expanded in later subtasks) --------------------------------

def main() -> None:
    script_dir = Path(__file__).resolve().parent

    print()
    print(_c("1", "Second Brain Vault — init (v4)"))

    vault = resolve_vault_dir()
    print(_c("2", f"target: {vault}"))
    print()


if __name__ == "__main__":
    main()
