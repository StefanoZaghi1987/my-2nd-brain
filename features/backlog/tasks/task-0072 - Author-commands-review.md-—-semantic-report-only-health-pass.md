---
id: TASK-0072
title: 'Author commands/review.md — semantic, report-only health pass'
status: To Do
assignee: []
created_date: '2026-05-29 11:44'
labels: []
milestone: m-1
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - commands/review.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create `commands/review.md` — the protocol for the new REVIEW operation. REVIEW is the LLM-judgment counterpart to the deterministic LINT: it covers semantic health checks that LINT's deterministic-only rule structurally excludes.

Three checks to define:
- **Check A — Contradictions**: pages making mutually inconsistent claims about the same named entity (person, org, date, version). Report: entity, page A claim + citation, page B claim + citation, proposed resolution.
- **Check B — Claim↔source faithfulness** (sampled, default 10 pages per run; configurable via `review.max_faithfulness_pages`): verify each wiki claim actually traces to its cited `raw/` source. Flags paraphrase drift, wrong citations, unsupported claims.
- **Check C — Summary quality**: flag thin summaries (< ~3 substantive sentences), copied text (violating Invariant #3), summaries with no cross-links.

Posture: **report-only** — proposes fixes, never applies them. Unattended-safe.

Scoping (controls cost — no O(n²) pairwise scan):
- Default: pages with `updated` newer than `last_review` in `.review/state.yaml`
- Explicit: `/review <topic|tag>` scopes to a cluster
- Full sweep: `/review --all` (asks user to confirm; expensive)

Protocol steps (9 steps as defined in the spec).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/review.md exists and defines the full 9-step protocol
- [ ] #2 All three checks (contradictions, faithfulness, quality) are described with their output format
- [ ] #3 Scoping behaviour (default/topic/--all) is documented with cost implications
- [ ] #4 Report-only posture is explicit: the command proposes fixes and never applies them
- [ ] #5 The command notes it writes .review/report.md and updates .review/state.yaml and wiki/log.md
<!-- AC:END -->
