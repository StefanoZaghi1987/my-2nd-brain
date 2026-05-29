#!/usr/bin/env python3
"""
yamlmini.py — Shared zero-dependency YAML parser for vault scripts.

Handles:
  - Scalars: bool (true/false), null/None/~/empty, int, string
  - Inline lists: key: [a, b, c]
  - Block lists:  key:\n  - a\n  - b
  - Two-level nesting: section:\n  subkey: value
  - Inline comments: key: value  # comment (outside quoted strings)

Does NOT handle: anchors, multi-line strings, 3+ level nesting.

This is the authoritative parser. vault_state and lint delegate to it.
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Scalar coercion
# ---------------------------------------------------------------------------

def _parse_scalar(val: str) -> Any:
    """Coerce a stripped string to the appropriate Python type."""
    if val in ("true", "True"):
        return True
    if val in ("false", "False"):
        return False
    if val in ("null", "Null", "None", "~", ""):
        return None
    try:
        return int(val)
    except ValueError:
        pass
    return val.strip("\"'")


# ---------------------------------------------------------------------------
# Block-list helpers
# ---------------------------------------------------------------------------

def _collect_block_list(lines: list[str], start: int) -> tuple[list[Any], int]:
    """Collect consecutive ``- item`` lines starting from index ``start``.

    Skips blank lines. Stops at the first non-blank non-list line.
    Returns ``(items, next_index)`` where next_index is the first line
    NOT consumed.
    """
    items: list[Any] = []
    j = start
    while j < len(lines):
        nxt = lines[j]
        if not nxt.strip():
            j += 1
            continue
        m = re.match(r"^\s*-\s+(.+)$", nxt)
        if m:
            item = m.group(1).strip()
            # Strip surrounding quotes before scalar coercion
            if (item.startswith('"') and item.endswith('"')) or \
               (item.startswith("'") and item.endswith("'")):
                item = item[1:-1]
            items.append(_parse_scalar(item))
            j += 1
        else:
            break
    return items, j


def _peek_next_line_type(lines: list[str], start: int) -> str:
    """Classify the first non-blank line at or after ``start``.

    Returns one of:
      ``'block-item'``   — line matches ``- value``
      ``'indented-key'`` — line is indented with ``key: value``
      ``'other'``        — top-level line or end of input
    """
    for line in lines[start:]:
        if not line.strip():
            continue
        if re.match(r"^\s+-\s+", line):
            return "block-item"
        if line[:1] in (" ", "\t"):
            return "indented-key"
        return "other"
    return "other"


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_yaml(text: str) -> dict:
    """Parse a two-level YAML-like string and return a nested dict.

    Designed as a strict superset of both:
    - ``vault_state._parse_config_yaml`` (2-level nesting + inline lists)
    - ``lint.parse_frontmatter`` (flat scalars + block lists)
    """
    result: dict = {}
    lines = text.splitlines()
    current_section: str | None = None
    i = 0

    while i < len(lines):
        raw_line = lines[i]
        stripped = raw_line.strip()

        # Skip blank and comment lines
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Skip standalone block-list items (consumed by the block-list handler)
        if re.match(r"^\s*-\s+", raw_line) and ":" not in stripped:
            i += 1
            continue

        if ":" not in stripped:
            i += 1
            continue

        key, _, val_raw = stripped.partition(":")
        key = key.strip()
        val = val_raw.strip()

        # Strip trailing inline comment, but only outside a quoted value
        if not (val.startswith('"') or val.startswith("'")):
            val = val.partition(" #")[0].strip()
            val = val.partition("\t#")[0].strip()

        is_indented = raw_line[:1] in (" ", "\t")

        if not is_indented:
            # ── Top-level key ─────────────────────────────────────────────
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                result[key] = [
                    _parse_scalar(x.strip().strip("\"'"))
                    for x in inner.split(",") if x.strip()
                ]
                current_section = None
                i += 1

            elif val == "":
                # Disambiguate: block-list header vs section header vs empty
                next_type = _peek_next_line_type(lines, i + 1)
                if next_type == "block-item":
                    items, next_i = _collect_block_list(lines, i + 1)
                    result[key] = items
                    current_section = None
                    i = next_i
                elif next_type == "indented-key":
                    result[key] = {}
                    current_section = key
                    i += 1
                else:
                    # No indented sub-keys or block items follow.
                    # Treat as an empty section header (matches old _parse_config_yaml
                    # which unconditionally opened {} for every empty top-level key).
                    result[key] = {}
                    current_section = key
                    i += 1

            else:
                result[key] = _parse_scalar(val)
                current_section = None
                i += 1

        elif current_section is not None:
            # ── Indented key under a known section ────────────────────────
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                result[current_section][key] = [
                    _parse_scalar(x.strip().strip("\"'"))
                    for x in inner.split(",") if x.strip()
                ]
                i += 1

            elif val == "":
                # Block list under a section key
                items, next_i = _collect_block_list(lines, i + 1)
                result[current_section][key] = items if items else None
                i = next_i

            else:
                result[current_section][key] = _parse_scalar(val)
                i += 1

        else:
            # Indented line with no active section context — skip
            i += 1

    return result


def parse_frontmatter(text: str) -> dict:
    """Extract and parse the YAML frontmatter block from a Markdown string.

    Returns an empty dict when no ``---`` frontmatter block is found.
    The rest of the document (body) is ignored.
    """
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    return parse_yaml(m.group(1))
