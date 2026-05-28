---
id: TASK-0053
title: Create init_vault.py — cross-platform vault bootstrap (parent task)
status: Done
assignee: []
created_date: '2026-05-28 16:06'
updated_date: '2026-05-28 17:08'
labels:
  - portability
  - new-file
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - init_vault.py
priority: high
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
New file `init_vault.py` at the repo root, parallel to `init-vault.sh`. Implemented in Python stdlib only (no pip deps), making it runnable on Linux, Windows+WSL, and native Windows without WSL. `init-vault.sh` is kept unchanged — existing Unix users are unaffected.

Interface (identical to init-vault.sh):
```
python3 init_vault.py                  # creates ./second-brain-vault
python3 init_vault.py /path/to/vault   # explicit path
python3 init_vault.py --here           # current directory
python3 init_vault.py --help
```

Key platform decisions:
- ANSI colors via escape codes, disabled when not sys.stdout.isatty()
- Symlinks: os.symlink() with except (OSError, NotImplementedError, PermissionError) → shutil.copy2() silently
- chmod +x: os.chmod(path, 0o755) guarded by os.name != "nt"
- Python dep check: subprocess.run([sys.executable, "-c", "import pkg"])
- Git identity: check user.name/email before committing; skip commit with warning if absent
- "Next steps" python cmd: "python3" on Unix, "python" on Windows

This parent task tracks the overall creation. Subtasks implement each functional section.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 python3 init_vault.py --help prints usage matching init-vault.sh --help
- [ ] #2 python3 init_vault.py --here on a clean directory creates a complete vault matching init-vault.sh output
- [ ] #3 python3 init_vault.py is safe to re-run (idempotent)
- [ ] #4 Script uses only Python stdlib — no pip install required to run init_vault.py itself
- [ ] #5 All subtasks completed
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created init_vault.py (~310 lines, stdlib only) as a full cross-platform port of init-vault.sh. All 8 subtasks completed with individual commits. The script is idempotent, handles Windows symlink fallback silently, uses os.name checks for chmod and py_cmd, checks git identity before committing, and uses sys.executable for all dep checks. Critical constraints verified: fetches_since_last_lint: 0, no frontmatter in _HOT_MD, python3 path in _LINT_REPORT.
<!-- SECTION:FINAL_SUMMARY:END -->
