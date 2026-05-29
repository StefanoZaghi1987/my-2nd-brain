#!/usr/bin/env python3
"""
console.py — Shared console utilities for vault scripts.

Call ensure_utf8_stdout() once at the top of any script that prints
unicode symbols (✓, ⚠, ·, →) to avoid UnicodeEncodeError on
cp1252 Windows consoles.

Note: init_vault.py intentionally keeps its own inline copy of this
logic because it must run BEFORE the shared scripts are installed.
"""

from __future__ import annotations

import sys


def ensure_utf8_stdout() -> None:
    """Reconfigure stdout/stderr to UTF-8 if not already.

    Safe to call multiple times (no-op when encoding is already UTF-8).
    Falls back gracefully on AttributeError / OSError (e.g., pipes).
    """
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")   # type: ignore[union-attr]
            sys.stderr.reconfigure(encoding="utf-8")   # type: ignore[union-attr]
        except (AttributeError, OSError):
            pass
