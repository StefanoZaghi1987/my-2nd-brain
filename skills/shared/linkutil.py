#!/usr/bin/env python3
"""linkutil.py — Canonical wikilink regex and path-resolution for the LLM Wiki engine.

Centralises the wikilink pattern and link-target resolution logic so that
both the vault linter and the backlink finder always use the same rules.
Previously these were copy-pasted in two files with a "keep in sync" comment.
"""
from __future__ import annotations
import re
from pathlib import Path

# Alias-aware wikilink regex — matches [[target]] and [[target|display label]].
WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")


def normalize_link_target(target: str, vault_root: Path, source_file: Path) -> Path | None:
    """Resolve a [[link]] target into an absolute path, or None if unresolvable.

    Tries target vault-relative, then source-relative. Also tries with .md
    appended when the path has no .md suffix — slugs like arxiv-2602.20867
    look like they have an extension but don't.
    """
    target = target.strip()
    if not target:
        return None
    base = Path(target)
    candidates = [base]
    if base.suffix != ".md":
        candidates.append(base.with_name(base.name + ".md"))
    for cand in candidates:
        abs_vault = vault_root / cand
        if abs_vault.exists():
            return abs_vault
        abs_local = source_file.parent / cand
        if abs_local.exists():
            return abs_local.resolve()
    # Return first candidate vault-relative as a fallback for error reporting.
    return vault_root / candidates[0]
