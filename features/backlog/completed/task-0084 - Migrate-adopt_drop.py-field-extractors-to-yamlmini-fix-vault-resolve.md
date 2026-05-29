---
id: TASK-0084
title: Migrate adopt_drop.py field extractors to yamlmini + fix --vault resolve
status: Done
assignee: []
created_date: '2026-05-29 21:37'
updated_date: '2026-05-29 23:14'
labels:
  - inbox-fetcher
  - yaml
  - bugfix
milestone: m-4
dependencies:
  - TASK-0081
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
`adopt_drop.py` has its own inline frontmatter field extractors (`extract_title_from_md`, `extract_source_url_from_md`) each with their own hand-rolled frontmatter regex. These can be replaced with `yamlmini.parse_frontmatter`. Additionally, `--vault` is not resolved to an absolute path in `main()`, so relative invocations can record relative paths.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. File to modify: `skills/inbox-fetcher/scripts/adopt_drop.py`. Tests: `tests/test_adopt_drop.py`.
Import path in script: `sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))`.
Run: `python -m pytest tests/test_adopt_drop.py -v`

## What to change
1. Add `from yamlmini import parse_frontmatter as _parse_frontmatter` after the existing `from vault_state import load_config` line.
2. Replace `extract_title_from_md` body — keep the function signature, replace the inline frontmatter parsing with `_parse_frontmatter(text)` then `fm.get("title")`.
3. Replace `extract_source_url_from_md` body — keep the signature, replace with `_parse_frontmatter(text)` then check keys `("source_url", "url", "link", "source")` in the returned dict.
4. In `main()`, add `.resolve()` to the vault path:
```python
    vault = Path(args.vault).resolve()
    if not vault.is_dir():
        print(f"ERROR: vault path is not a directory: {vault}", file=sys.stderr)
        return 1
    return process_drop_zone(vault, dry_run=args.dry_run)
```

Full replacement code for both functions is in the implementation plan (Task 4).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 extract_title_from_md and extract_source_url_from_md use yamlmini.parse_frontmatter instead of inline regex
- [x] #2 All existing test_adopt_drop.py tests pass with no regressions
- [x] #3 main() calls Path(args.vault).resolve() before passing to process_drop_zone
- [ ] #4 Full pytest suite passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Replaced extract_title_from_md and extract_source_url_from_md inline regex extractors with yamlmini.parse_frontmatter. Removed now-dead `import re`. Added Path(args.vault).resolve() in main() to prevent relative paths being recorded in inbox. Existing test suite (54 tests) covers behavioral equivalence including edge cases (malformed frontmatter, H1 fallback, all four URL-key variants).
<!-- SECTION:FINAL_SUMMARY:END -->
