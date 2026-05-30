---
id: TASK-0094
title: 'Task 4: Create commands/expand.md'
status: Done
assignee: []
created_date: '2026-05-30 22:09'
updated_date: '2026-05-30 22:38'
labels:
  - commands
  - expand
milestone: m-5
dependencies: []
references:
  - >-
    features/specs/2026-05-30-ingest-depth-coverage-design.md#33-new-expand-page-command-depth-fix
  - >-
    features/plans/2026-05-30-ingest-depth-coverage.md#task-4--create-commandsexpandmd
  - features/prompts/expand-command-template.md
modified_files:
  - commands/expand.md
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the new /expand command by copying features/prompts/expand-command-template.md verbatim to commands/expand.md. Follows the /refresh command anatomy: description frontmatter, H1, Arguments, Protocol (6 numbered ### steps), Guards, Unattended mode, What /expand does NOT do, Report format.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 File begins with YAML frontmatter (description: key)
- [x] #2 H1 is '# /expand — Deepen a wiki page'
- [x] #3 Protocol has 6 numbered ### steps
- [x] #4 Step 5 handles both absent and already-exists cases for ## Deep dive
- [x] #5 Step 5 shows expanded: YYYY-MM-DD frontmatter key in yaml code block
- [x] #6 Guards, Unattended mode, What /expand does NOT do, Report format sections all present
- [x] #7 Report format ends with '→ Run /review to find other pages worth expanding'
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
commands/expand.md created from template (462a9f3) + quality fixes (a57929c): removed dead Windows note, fixed fanout count (added index+log to formula), hardened unattended refusal with concrete message, added idempotency coverage for partial sections, made wiki/index.md marker idempotent.
<!-- SECTION:FINAL_SUMMARY:END -->
