---
id: TASK-0089
title: >-
  Update init_vault.py to install yamlmini.py and console.py into generated
  vaults
status: Done
assignee: []
created_date: '2026-05-29 21:38'
updated_date: '2026-05-29 23:14'
labels:
  - installer
  - bugfix
milestone: m-4
dependencies:
  - TASK-0081
  - TASK-0085
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: high
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
`init_vault.py` copies shared scripts into every generated vault's `.claude/skills/shared/` via the `_SHARED_SCRIPTS` list (line 365). After Tasks 0081 and 0085 added `yamlmini.py` and `console.py` to `skills/shared/`, they must be added to this list or deployed vaults won't receive them.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. File: `init_vault.py` line 365.
Current list:
```python
_SHARED_SCRIPTS = ["vault_state.py", "review_scope.py", "find_backlinks.py", "linkutil.py"]
```
Run: `python -m pytest tests/test_installer.py tests/test_bootstrap.py -v`

## Fix
Change line 365 to:
```python
_SHARED_SCRIPTS = [
    "vault_state.py",
    "yamlmini.py",
    "console.py",
    "review_scope.py",
    "find_backlinks.py",
    "linkutil.py",
]
```

Then run the smoke test to verify both files land in the generated vault:
```powershell
python init_vault.py ./tmp-smoke --yes
ls ./tmp-smoke/.claude/skills/shared/
Remove-Item -Recurse -Force ./tmp-smoke
```
Expected: `yamlmini.py` and `console.py` appear in the listing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 _SHARED_SCRIPTS in init_vault.py includes yamlmini.py and console.py
- [x] #2 Bootstrap smoke test: python init_vault.py ./tmp-smoke --yes produces a vault where both files exist in .claude/skills/shared/
- [x] #3 All test_installer.py and test_bootstrap.py tests pass
- [ ] #4 Full pytest suite passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added yamlmini.py and console.py to _SHARED_SCRIPTS list in init_vault.py (now 6 entries). Both files are present in skills/shared/ for the installer to copy. Added test_yes_flag_deploys_yamlmini_and_console to test_bootstrap.py as a regression guard (follows the pattern of test_yes_flag_deploys_linkutil).
<!-- SECTION:FINAL_SUMMARY:END -->
