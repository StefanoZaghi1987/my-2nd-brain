---
id: TASK-0068
title: >-
  Replace Path.rename() with shutil.move() in adopt_drop.py for cross-filesystem
  safety
status: To Do
assignee: []
created_date: '2026-05-29 11:43'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - skills/inbox-fetcher/scripts/adopt_drop.py
  - tests/test_adopt_drop.py
priority: medium
ordinal: 1700
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`skills/inbox-fetcher/scripts/adopt_drop.py` moves adopted files from `raw/drop/` to `raw/local/<slug>/` using `Path.rename()` (line ~147). On Windows this raises `OSError` when source and destination are on different volumes; on Linux it raises `OSError: [Errno 18] Invalid cross-device link`. This is a real failure mode when the drop zone is configured on a separate mount or drive.

Replace the `rename()` call with `shutil.move(str(src), str(dst))`, which handles cross-filesystem moves transparently (copy + delete). Add a WHY comment explaining that `shutil.move` is needed because `Path.rename()` does not work across filesystems.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 adopt_drop.py uses shutil.move() instead of Path.rename() for the file adoption step
- [ ] #2 A comment near the call explains why shutil.move is used rather than Path.rename
- [ ] #3 One new test mocks Path.rename to raise OSError(18, 'Invalid cross-device link') and asserts adoption still succeeds via shutil.move
- [ ] #4 Existing adoption tests (happy path, rollback on failure) remain green
<!-- AC:END -->
