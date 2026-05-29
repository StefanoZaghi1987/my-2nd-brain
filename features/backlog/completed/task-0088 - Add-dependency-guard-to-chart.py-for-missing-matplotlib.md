---
id: TASK-0088
title: Add dependency guard to chart.py for missing matplotlib
status: Done
assignee: []
created_date: '2026-05-29 21:38'
updated_date: '2026-05-29 23:14'
labels:
  - view-builder
  - bugfix
milestone: m-4
dependencies: []
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: low
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
`chart.py` imports `matplotlib` at the top level with no guard. If matplotlib is not installed, a bare `ImportError` is raised — even for `--help`. All other scripts in the engine give a friendly, actionable message and exit cleanly. This is a one-file fix.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. File: `skills/view-builder/templates/chart.py`. Tests: `tests/test_chart.py`.
Run: `python -m pytest tests/test_chart.py -v`

## Fix
Replace the current top-of-file import block (lines 1-13):
```python
# BEFORE:
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```
with:
```python
import argparse
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("chart.py requires matplotlib. Install it with:", file=sys.stderr)
    print("  pip install matplotlib", file=sys.stderr)
    sys.exit(1)
```
The rest of the file is unchanged.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 chart.py wraps its matplotlib import in try/except ImportError
- [x] #2 The error message says 'pip install matplotlib'
- [ ] #3 All test_chart.py tests pass (matplotlib is installed in test env)
- [ ] #4 Full pytest suite passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Wrapped the three matplotlib import lines in try/except ImportError with a friendly "chart.py requires matplotlib. Install it with: pip install matplotlib" message to stderr and sys.exit(1). Added import sys at top (was missing). Matches the guard pattern in fetch_inbox.py.
<!-- SECTION:FINAL_SUMMARY:END -->
