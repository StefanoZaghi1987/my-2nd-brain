---
id: TASK-0067
title: Graceful degradation when a lint check throws in lint.py
status: To Do
assignee: []
created_date: '2026-05-29 11:43'
updated_date: '2026-05-29 12:04'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - skills/vault-linter/scripts/lint.py
  - tests/test_lint.py
priority: medium
ordinal: 1600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In `skills/vault-linter/scripts/lint.py`, the `all_checks` loop (line ~805) runs each check function without a try/except. If any single check raises an uncaught exception, the entire lint run aborts with exit code 2 — one edge-case check kills the whole health report.

Wrap each check invocation in a try/except so a crashing check is recorded as an advisory finding (`"check crashed: <check_name>: <exc>"`) and the loop continues. Exit code 2 should be reserved for catastrophic failure (e.g., vault path doesn't exist, no checks completed at all).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 When one check function raises an exception, the lint run continues and other checks produce results
- [ ] #2 The crashed check appears in the report as an advisory finding with the check name and exception message
- [ ] #3 Exit code is 1 (findings present) when some checks pass and one crashes; not 2
- [ ] #4 Exit code 2 is only returned when no checks complete at all (e.g., vault missing)
- [ ] #5 One new test injects a mock check that raises; asserts exit 1 and the crash advisory in output
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Key implementation details for a fresh agent:

**Finding dataclass** (lint.py line 69) has fields: `severity`, `check`, `file`, `detail`, `line`. The field is `detail`, NOT `message`.

**all_checks is a local variable** inside `run_lint()` (line 787) — it cannot be patched as a module attribute. To test graceful degradation, patch an existing check function at module level, e.g.:
```python
import unittest.mock as mock
import lint as lint_mod
with mock.patch.object(lint_mod, "check_gaps", side_effect=RuntimeError("crash")):
    exit_code = run_lint(vault_path, quiet=True)
```

**Implementation pattern**: initialize `out: list[Finding] = []` BEFORE the try block so the print statement always has a valid `len(out)`. Build the crash advisory as a Finding in `out`, extend findings, then continue the loop. Add `completed` counter and check `if completed == 0: return 2` AFTER the loop (not inside it).

**Test imports** use the sys.path.insert pattern already in test_lint.py (line 5):
`sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "vault-linter" / "scripts"))`
Then: `from lint import run_lint`
<!-- SECTION:NOTES:END -->
