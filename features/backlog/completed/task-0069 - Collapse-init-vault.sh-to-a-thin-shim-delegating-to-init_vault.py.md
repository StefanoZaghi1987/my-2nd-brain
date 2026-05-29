---
id: TASK-0069
title: Collapse init-vault.sh to a thin shim delegating to init_vault.py
status: Done
assignee: []
created_date: '2026-05-29 11:43'
updated_date: '2026-05-29 15:03'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - init-vault.sh
priority: medium
ordinal: 1800
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`init-vault.sh` is a full parallel bootstrapper that has drifted from `init_vault.py` (the canonical, maintained path). It is missing `adopt_drop.py` installation, missing `raw/local/` and `raw/drop/` directory creation, and contains stale text ("four commands", "drop in raw/papers/"). Re-synchronising two bootstrappers will just recreate the drift after the next feature.

Replace the entire `init-vault.sh` body with a thin shim that passes all arguments to `python3 init_vault.py "$@"`. This permanently eliminates the source of drift — there is only one bootstrapper to maintain.

The shim should include a brief comment explaining it delegates to the Python bootstrapper and why (single source of truth).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 init-vault.sh is a short script (< 10 lines) that calls python3 init_vault.py with all arguments forwarded
- [x] #2 Running ./init-vault.sh <tmp_dir> and python init_vault.py <tmp_dir> produce identical vault structures including adopt_drop.py, raw/local/, and raw/drop/
- [x] #3 A comment explains why this is a shim rather than a standalone implementation
- [x] #4 init-vault.sh remains executable (chmod +x preserved)
<!-- AC:END -->



## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Replaced 396-line stale bootstrapper with 6-line shim using $(dirname $0) path resolution and set -euo pipefail. git mode 100755 preserved. Smoke test verified Python path installs adopt_drop.py + raw/local/ + raw/drop/. Commit aa95880.
<!-- SECTION:FINAL_SUMMARY:END -->
