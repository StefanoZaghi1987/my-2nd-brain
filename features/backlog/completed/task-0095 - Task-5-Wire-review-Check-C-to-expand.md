---
id: TASK-0095
title: 'Task 5: Wire /review Check C to /expand'
status: Done
assignee: []
created_date: '2026-05-30 22:09'
updated_date: '2026-05-30 22:40'
labels:
  - commands
  - review
milestone: m-5
dependencies: []
references:
  - >-
    features/specs/2026-05-30-ingest-depth-coverage-design.md#35-review-becomes-the-depth-driver-commandsreviewmd
  - >-
    features/plans/2026-05-30-ingest-depth-coverage.md#task-5--wire-review-check-c-to-expand
modified_files:
  - commands/review.md
priority: medium
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
One-line change in commands/review.md step 9: replace 'consider expanding the summary or adding cross-links' with 'consider /expand <page> to deepen from the full source, or add cross-links'. Closes the detect→act loop so thin-page detection leads to a concrete action.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Step 9's Summary quality bullet mentions '/expand <page>'
- [x] #2 Contradictions and Faithfulness bullets are unchanged
- [x] #3 No other lines were modified
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
One-line change: Summary quality bullet now reads 'consider /expand <page> to deepen from the full source, or add cross-links'. Committed 03234af.
<!-- SECTION:FINAL_SUMMARY:END -->
