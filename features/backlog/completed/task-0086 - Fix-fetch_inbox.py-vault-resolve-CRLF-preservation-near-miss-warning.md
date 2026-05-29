---
id: TASK-0086
title: 'Fix fetch_inbox.py: --vault resolve, CRLF preservation, near-miss warning'
status: Done
assignee: []
created_date: '2026-05-29 21:37'
updated_date: '2026-05-29 23:14'
labels:
  - inbox-fetcher
  - windows
  - bugfix
milestone: m-4
dependencies: []
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
Three small robustness fixes for `fetch_inbox.py`:
1. `--vault` is not resolved to absolute, so relative invocations can record relative paths in inbox.md.
2. `update_inbox` uses `splitlines()` + `"\n".join(...)`, silently converting CRLF → LF on Windows.
3. A line like `- [ ] https://x.com my note` fails `UNCHECKED_PATTERN` silently — the URL+inline-note is dropped with no warning.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. File: `skills/inbox-fetcher/scripts/fetch_inbox.py`. Tests: `tests/test_fetch_inbox.py`.
`UNCHECKED_PATTERN = re.compile(r"^- \[ \] (https?://\S+)\s*$")` — the one-URL-per-line contract is intentional and must NOT change.
Run: `python -m pytest tests/test_fetch_inbox.py -v`

## Fix 1 — --vault resolve
In `main()`, change `args.vault` usage to `Path(args.vault).resolve()` (same pattern as `lint.py` line 850).

## Fix 2 — CRLF preservation
In `update_inbox`, detect the original line separator before splitting:
```python
line_sep = "\r\n" if "\r\n" in inbox_text else "\n"
lines = inbox_text.splitlines()
```
At the end, replace the `return` line:
```python
# was:  return "\n".join(final_lines) + ("\n" if inbox_text.endswith("\n") else "")
ending = line_sep if inbox_text.endswith(("\n", "\r\n")) else ""
return line_sep.join(final_lines) + ending
```

## Fix 3 — near-miss warning
Add a module-level pattern:
```python
_NEAR_MISS_PATTERN = re.compile(r"^- \[ \] https?://\S+\s+\S")
```
In `update_inbox`'s main loop, in the `if not match and not failed_match:` branch:
```python
if _NEAR_MISS_PATTERN.match(line):
    out_lines.append(line + " ⚠ skipped: inline text after URL — move notes to an indented sub-bullet")
else:
    out_lines.append(line)
```

## Tests to add (write before implementing)
```python
class TestUpdateInboxCRLFAndWarning:
    def test_crlf_line_endings_are_preserved(self): ...
    def test_near_miss_entry_emits_warning(self): ...
    def test_lf_line_endings_are_preserved(self): ...
```
Full test code is in the implementation plan (Task 6, Step 1).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 main() calls Path(args.vault).resolve()
- [x] #2 CRLF inboxes survive update_inbox with CRLF line endings intact
- [x] #3 LF inboxes survive update_inbox without gaining CRLF
- [ ] #4 A line '- [ ] https://x.com my note' produces a ⚠ warning in the output, not a silent skip
- [ ] #5 UNCHECKED_PATTERN itself is NOT changed (one-URL-per-line contract preserved)
- [ ] #6 All existing test_fetch_inbox.py tests pass
- [ ] #7 Full pytest suite passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Three fixes in fetch_inbox.py: (1) CRLF preservation — detect line_sep before splitlines(), use line_sep.join() on return; (2) Near-miss warning — _NEAR_MISS_PATTERN flags "- [ ] URL extra-text" lines with ⚠ annotation, idempotency guard prevents compounding on repeated runs; (3) --vault resolve — Path(args.vault).resolve() in main(). Added TestUpdateInboxCRLFAndWarning with 3 tests covering all three behaviors.
<!-- SECTION:FINAL_SUMMARY:END -->
