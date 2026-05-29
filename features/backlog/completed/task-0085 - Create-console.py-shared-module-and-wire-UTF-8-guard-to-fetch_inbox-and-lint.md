---
id: TASK-0085
title: Create console.py shared module and wire UTF-8 guard to fetch_inbox and lint
status: Done
assignee: []
created_date: '2026-05-29 21:37'
updated_date: '2026-05-29 23:14'
labels:
  - shared
  - windows
  - bugfix
milestone: m-4
dependencies: []
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
`fetch_inbox.py` and `lint.py` print unicode symbols (`✓`, `⚠`, `·`, `→`) to stdout with no UTF-8 guard. On a cp1252 Windows console this raises `UnicodeEncodeError`. `init_vault.py` already has the correct guard inline (lines 24-29), but it can't be reused — the bootstrapper must not import from the scripts it installs.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. `init_vault.py` L24-29 shows the pattern to replicate.
Files to create/modify:
- Create: `skills/shared/console.py`
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py` (add import + call at top)
- Modify: `skills/vault-linter/scripts/lint.py` (add import + call after yamlmini import — Task 0083 adds that import first)
Run: `python -m pytest tests/ -v`

## What to build

`skills/shared/console.py`:
```python
#!/usr/bin/env python3
"""console.py — Shared console utilities for vault scripts."""
from __future__ import annotations
import sys

def ensure_utf8_stdout() -> None:
    """Reconfigure stdout/stderr to UTF-8 if not already.
    Safe to call multiple times. init_vault.py intentionally keeps its own
    inline copy — the bootstrapper must not import from its own payload.
    """
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
```

In `fetch_inbox.py`, after the `sys.path.insert` and `from vault_state import ...` lines:
```python
from console import ensure_utf8_stdout
ensure_utf8_stdout()
```

In `lint.py`, after the `from yamlmini import parse_frontmatter` line:
```python
from console import ensure_utf8_stdout
ensure_utf8_stdout()
```

**Do NOT modify `init_vault.py`** — it must stay self-contained.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 skills/shared/console.py exists with ensure_utf8_stdout() function
- [x] #2 fetch_inbox.py imports and calls ensure_utf8_stdout() at module load
- [x] #3 lint.py imports and calls ensure_utf8_stdout() at module load
- [ ] #4 init_vault.py is NOT modified
- [ ] #5 Full pytest suite passes with no regressions
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created skills/shared/console.py with ensure_utf8_stdout() — uses sys.stdout.reconfigure(encoding="utf-8") with (AttributeError, OSError) fallback, safe to call multiple times. Wired into fetch_inbox.py and lint.py (both print unicode symbols). adopt_drop.py deliberately excluded (uses ASCII markers). init_vault.py keeps its own inline copy intentionally — must run before shared scripts are installed. console.py added to _SHARED_SCRIPTS so it deploys into every generated vault.
<!-- SECTION:FINAL_SUMMARY:END -->
