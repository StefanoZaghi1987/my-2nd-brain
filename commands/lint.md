---
description: Run deterministic health checks on the vault. Writes .lint/report.md.
  Checks dead links, orphans, duplicates, missing metadata, inconsistent naming,
  stale sources, gaps, view staleness, based_on dead links, and pdf folder structure.
  Auto-triggers based on thresholds in vault.config.yml.
---

# /lint — Run vault health checks

## When to use

Run explicitly with `/lint` or when the auto-trigger condition is met.

## Auto-trigger

At session start, check `.lint/state.yaml` for two conditions:

1. `ingests_since_last_lint` ≥ `lint.auto_trigger_after_ingests` (from vault.config.yml)
2. Days since `last_lint` ≥ `lint.auto_trigger_after_days` (from vault.config.yml)

If either condition is met, run lint before proceeding with the session.

## How to run

```bash
python .claude/skills/vault-linter/scripts/lint.py
```

Or from outside the vault:

```bash
python .claude/skills/vault-linter/scripts/lint.py --vault /path/to/vault
```

## Output

- `.lint/report.md` — findings grouped by severity (blocking / important / advisory)
- `.lint/state.yaml` — updated with run date and finding counts

## Severity levels

- **Blocking** — dead links, missing required metadata, broken based_on links. Fix before ingesting more.
- **Important** — orphan pages, gaps. Address when convenient.
- **Advisory** — duplicates, stale sources, naming inconsistencies. Use judgement.

## What the agent does with the report

**Interactive:** summarise findings ("X blocking, Y important, Z advisory"), offer to fix blocking issues.

**Unattended:** run and note summary in compass.md footer. Abort /reflect if blocking count > 50.

## Rules

- Does not fix anything — reports only.
- Does not use an LLM — pure Python on text and filesystem.
- Does not validate semantic content — that is /reflect's job.
