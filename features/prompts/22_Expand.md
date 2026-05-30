# Ingest Depth & Coverage

## Objective
Fix shallow wiki pages by (1) adding an adaptive page/source structure schema to `CLAUDE.md`, (2) replacing the fixed page-window PDF read in `/ingest` with a map-then-read protocol, (3) creating a new `/expand <page>` command that reads sources in full and appends a `## Deep dive` section on demand.

## Context
Read "D:\my-2nd-brain\features\specs\2026-05-30-ingest-depth-coverage-design.md" spec and related "D:\my-2nd-brain\features\plans\2026-05-30-ingest-depth-coverage.md" implementation plan.
Detailed aspects of the actual implementation must be inferred by analyzing the codebase.

---

**Planning Phase Required:**
1. Review design spec and implementation plan
2. Create detailed plan before implementation
3. Get plan approval before coding
4. Use superpowers:subagent-driven-development to implement this plan. Remember to keep backlog.md tasks updated.