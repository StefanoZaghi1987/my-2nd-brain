---
id: TASK-0014
title: Create commands/refresh.md slash command
status: Done
assignee: []
created_date: '2026-05-28 07:37'
updated_date: '2026-05-28 09:47'
labels:
  - feature-d
  - commands
milestone: features
dependencies: []
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: medium
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add `commands/refresh.md` following the structure of the existing command files. The command re-fetches a source whose content has changed and re-ingests it without losing the citation graph built on top.

Arguments: `/refresh <source>` — same forms as `/forget`: slug, wiki path, raw path, or URL.

Protocol to document:
1. Resolve slug; read `source_url` from `wiki/sources/<slug>.md`.
2. Add URL back to `inbox.md` as an unchecked entry under "To process".
3. Instruct user to run the fetcher script — it overwrites the raw folder.
4. Re-ingest: rewrite `wiki/sources/<slug>.md` with updated summary; bump `updated` date.
5. Scan `wiki/pages/` citing this source; append `#needs-review` tag to any claim that may have changed based on the diff between old and new summary.
6. Append to `log.md`: `## [YYYY-MM-DD] refresh | <slug>`.

Explicitly state what `/refresh` does NOT do: it does not auto-update page prose; step 5 only flags for user review.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/refresh.md exists with correct frontmatter and heading structure
- [ ] #2 All argument forms are documented (slug, wiki path, raw path, URL)
- [ ] #3 Protocol steps are numbered and match the design
- [ ] #4 Step 5 (flag changed claims with #needs-review) is explicit about flagging only, not rewriting
- [ ] #5 The NOT-scope section is present and clear
- [ ] #6 log.md update step is included
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 14** in the implementation plan. Full markdown content for `commands/refresh.md` is provided — copy verbatim. Key details: (1) source arg accepts slug, wiki path, raw path, or URL, (2) confirms resolved slug+URL with user before queuing, (3) flags citing pages with `needs-review` frontmatter tag (not inline annotation), (4) does NOT rewrite prose — flags only, (5) if >15 pages cite the source, report fanout and stop (invariant #5). Wave 2 — requires Wave 1 complete.
<!-- SECTION:NOTES:END -->
