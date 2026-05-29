#!/usr/bin/env python3
"""
vault_state.py — Config loading and vault state read/write.

Provides a single import point for vault.config.yml and .lint/state.yaml
so all scripts share the same config values and state schema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from yamlmini import parse_yaml as _parse_yaml


# ---------------------------------------------------------------------------
# Scalar coercion — kept local, NOT replaced with parse_yaml.
# read_state uses a hand-rolled line parser; parse_yaml would interpret an
# empty top-level value (e.g. "last_lint:") as a section header and return
# {"last_lint": {}}, breaking the None round-trip that write_state relies on.
# ---------------------------------------------------------------------------

def _parse_scalar(val: str) -> Any:
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
# Defaults — mirrors vault.config.yml; used when the file is absent
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, Any] = {
    "vault": {"version": 1},
    "inbox": {
        "processed_section": "## Processed",
        "tags_propagation": True,
    },
    "fetch": {
        "html_timeout_seconds": 20,
        "pdf_timeout_seconds": 60,
        "max_pdf_size_mb": 50,
        "pdf_enabled": True,
        "walled_domains": [
            "x.com", "twitter.com", "mobile.twitter.com",
            "linkedin.com", "www.linkedin.com", "threads.net",
            "facebook.com", "www.facebook.com",
            "instagram.com", "www.instagram.com",
        ],
    },
    "lint": {
        "stale_source_days": 180,
        "view_stale_days": 30,
        "auto_trigger_after_fetches": 5,
        "auto_trigger_after_days": 7,
        "reflect_reminder_days": 14,
    },
    "ingest": {
        "max_new_pages_before_confirm": 3,
        "max_files_per_operation": 15,
    },
    "drop_zone": {
        "path": "raw/drop",
        "enabled": True,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def load_config(vault_root: Path) -> dict:
    """Load vault.config.yml and deep-merge with built-in defaults.

    Returns defaults silently when the file is absent (backward-compatible).
    Raises ValueError when the file exists but cannot be read or parsed.
    """
    config_path = vault_root / "vault.config.yml"
    if not config_path.exists():
        return _deep_merge(_DEFAULTS, {})
    try:
        text = config_path.read_text(encoding="utf-8")
        parsed = _parse_yaml(text)
    except Exception as exc:
        raise ValueError(f"vault.config.yml cannot be loaded: {exc}") from exc
    return _deep_merge(_DEFAULTS, parsed)


def read_state(vault_root: Path) -> dict:
    """Read .lint/state.yaml into a flat dict with typed values.

    Returns an empty dict when the file is absent.
    Values are coerced: null/empty → None, true/false → bool, integers → int.
    """
    state_path = vault_root / ".lint" / "state.yaml"
    if not state_path.exists():
        return {}
    result: dict = {}
    for line in state_path.read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, _, v = line.partition(":")
            result[k.strip()] = _parse_scalar(v.strip())
    return result


def write_state(vault_root: Path, updates: dict) -> None:
    """Patch .lint/state.yaml with the given key-value pairs.

    Existing keys not in updates are preserved; new keys are added.
    Creates .lint/ and state.yaml if absent.
    None values are written as empty strings (so they round-trip back as None).
    """
    lint_dir = vault_root / ".lint"
    lint_dir.mkdir(exist_ok=True)
    current = read_state(vault_root)
    for k, v in updates.items():
        current[str(k)] = v
    lines = []
    for k, v in current.items():
        lines.append(f"{k}: {'' if v is None else v}")
    (lint_dir / "state.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
