---
id: TASK-0017
title: Add text fallback to view-concept-map.md template
status: To Do
assignee: []
created_date: '2026-05-28 07:41'
updated_date: '2026-05-28 08:26'
labels:
  - feature-f
  - view-builder
milestone: features
dependencies: []
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: low
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend `skills/view-builder/templates/view-concept-map.md` by adding a `<details>` adjacency list block immediately after the Mermaid diagram block.

The `<details>` section uses `<summary>Text fallback</summary>` as its header and contains a plain markdown bullet list of directed edges in the form `- Node A → Node B`. This renders as a collapsible block in Obsidian and GitHub, and degrades to visible plain text in environments that do not support HTML details tags.

The template placeholder comments must make clear that both blocks must be filled from the same data — same nodes, same edges, different representation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Template contains a Mermaid block followed immediately by a <details> block
- [ ] #2 The <details> block uses the exact header: <summary>Text fallback</summary>
- [ ] #3 Placeholder comments instruct the agent to keep Mermaid and adjacency list in sync
- [ ] #4 The template remains valid markdown when the HTML tags are ignored by renderers that don't support them
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 17** in the implementation plan. Two changes: (1) in `skills/view-builder/templates/view-concept-map.md`, insert a `<details><summary>Text fallback</summary>` block immediately after the closing triple-backtick of the Mermaid block — exact content provided; (2) in `skills/view-builder/SKILL.md` Rules section, add a concept-map sync rule stating both blocks must be populated from the same data. Wave 3 — independent, no dependencies.
<!-- SECTION:NOTES:END -->
