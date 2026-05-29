---
id: TASK-0082
title: Migrate vault_state.py to yamlmini and fix null round-trip in read/write_state
status: Done
assignee: []
created_date: '2026-05-29 21:36'
updated_date: '2026-05-29 23:14'
labels:
  - shared
  - yaml
  - bugfix
milestone: m-4
dependencies:
  - TASK-0081
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
`vault_state._parse_config_yaml` is the old 2-level YAML parser that lacks block-list support. Task 0081 created the replacement (`yamlmini.parse_yaml`). This task migrates `vault_state` to use it, and also fixes a second bug: `read_state` returns ALL values as strings, so `last_lint: null` round-trips as the string `"null"` not Python `None` — corrupting first-run date logic.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. File to modify: `skills/shared/vault_state.py`. Tests: `tests/test_vault_state.py`.
Test import: `sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))` then `from vault_state import load_config, read_state, write_state`.
Run: `python -m pytest tests/test_vault_state.py -v`

## What to change
1. Replace `_parse_config_yaml` call in `load_config` with `yamlmini.parse_yaml`. Import: `from yamlmini import parse_yaml as _parse_yaml`. Keep `_parse_scalar` as a local copy in vault_state.py (do NOT import it from yamlmini as it's a private function).
2. In `read_state`, coerce each value through `_parse_scalar(v.strip())` so null/bool/int survive correctly.
3. In `write_state`, write `None` values as empty string (`f"{k}: "` not `f"{k}: None"`).

## Tests to add (write before implementing)
Add to `tests/test_vault_state.py::TestWriteState`:
```python
def test_null_value_round_trips_as_none(self, tmp_path):
    write_state(tmp_path, {"last_lint": None})
    state = read_state(tmp_path)
    assert state["last_lint"] is None

def test_date_string_round_trips_unchanged(self, tmp_path):
    write_state(tmp_path, {"last_lint": "2026-01-15"})
    state = read_state(tmp_path)
    assert state["last_lint"] == "2026-01-15"
```
Add to `TestLoadConfig`:
```python
def test_block_list_walled_domains(self, tmp_path):
    (tmp_path / "vault.config.yml").write_text(
        "fetch:\n  walled_domains:\n    - x.com\n    - twitter.com\n    - linkedin.com\n"
    )
    config = load_config(tmp_path)
    assert config["fetch"]["walled_domains"] == ["x.com", "twitter.com", "linkedin.com"]
```

Full replacement code for vault_state.py is in the implementation plan (Task 2).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 test_null_value_round_trips_as_none passes: write_state(None) then read_state returns Python None not the string 'null'
- [x] #2 test_block_list_walled_domains passes: block-list walled_domains config parses to a proper list
- [x] #3 All existing test_vault_state.py tests still pass (no regressions)
- [ ] #4 Full pytest suite passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Replaced _parse_config_yaml with yamlmini.parse_yaml in vault_state.py. Fixed read_state to coerce values through _parse_scalar (null→None, true/false→bool, int→int). Fixed write_state to serialize None as empty string (not "null") so null values round-trip correctly. _parse_scalar kept local with explanatory comment: cannot use parse_yaml because read_state is a line parser and parse_yaml would interpret empty top-level values as section headers. Added 5 new tests including null/bool round-trips and the headline walled_domains block-list regression guard.
<!-- SECTION:FINAL_SUMMARY:END -->
