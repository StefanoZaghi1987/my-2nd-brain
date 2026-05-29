---
description: Semantic health pass over the vault wiki. Runs three LLM-judgment
  checks (contradictions, claim-source faithfulness, summary quality) that the
  deterministic LINT cannot cover. Report-only — proposes fixes, never applies
  them. Scoped to changed pages by default to keep token cost bounded.
---

# /review — Semantic health pass

Run when you want to catch contradictions between pages, verify that wiki
claims actually trace to their cited sources, or surface thin/copied summaries.
This is the LLM-judgment counterpart to the deterministic `/lint`.

## When to use

- After ingesting several new sources that touch overlapping topics.
- When a `/lint` run surfaces near-duplicate pages (`check_duplicates`) and
  you want to check whether they actually contradict each other.
- Periodically on a slow-growing vault, or whenever you suspect paraphrase
  drift has crept in.
- `/review --all` for a full sweep (expensive — confirm with the user first).

## Scoping

| Invocation | Scope |
|---|---|
| `/review` (default) | Pages whose `updated` date is strictly after `last_review` in `.review/state.yaml`. If no prior run, covers all pages. |
| `/review <topic-or-tag>` | Pages matching that tag, or pages that link to the named topic page. |
| `/review --all` | All wiki pages. Expensive — ask the user to confirm before starting. |

## Three checks

### Check A — Contradictions

For each pair of pages in scope that both mention the same named entity
(person, organisation, project, date, version number):

Entity detection should focus on proper nouns and versioned identifiers (e.g., "GPT-4", "OpenAI", "v3.2"). Bare years or generic dates should only be compared when both appear in the same semantic context (e.g., both attributed to the same product release or event).

- Read the relevant claim in each page.
- If the two claims are mutually inconsistent (e.g. different founding years,
  conflicting capability descriptions, opposing conclusions), record a finding.
- **Finding format:**
  ```
  Entity: <name>
  Page A: wiki/pages/foo.md — "<claim text>" (cites: raw/web/foo-slug/)
  Page B: wiki/pages/bar.md — "<claim text>" (cites: raw/papers/bar-slug/)
  Proposed resolution: <one-sentence suggestion, e.g. "check source X — it
  was published later and supersedes the earlier claim">
  ```

### Check B — Claim↔source faithfulness

For a sample of pages from the scope (up to `review.max_faithfulness_pages`
pages, default 10 if the key is absent; configurable in `vault.config.yml`
under `review: max_faithfulness_pages:`):

- For each claim that cites a `raw/` source via a `[[wiki/sources/...]]` link
  or a direct `raw/` path:
  - Read the cited source.
  - Verify the claim is a faithful paraphrase of what the source says.
- Flag cases where:
  - The paraphrase has drifted and no longer reflects the source.
  - The citation points to a source that doesn't mention the claim.
  - A claim appears to have no traceable support at all (Invariant #2 breach).
- **Finding format:**
  ```
  Page: wiki/pages/foo.md
  Claim: "<claim text>"
  Cited source: raw/web/foo-slug/
  Issue: <paraphrase drift | wrong citation | unsupported claim>
  Proposed action: <edit the claim | re-read the source | add a citation>
  ```

### Check C — Summary quality

For all pages in scope, flag summaries that are:
- **Thin**: fewer than ~3 substantive sentences of actual content.
- **Copied**: appear to reproduce source text verbatim (violates Invariant #3).
- **Unlinked**: contain no `[[wikilink]]` cross-references to other pages
  (the deterministic linter's `missing_cross_references` check is the
  cheaper complement; this check catches cases it misses).
- **Finding format:**
  ```
  Page: wiki/pages/foo.md
  Issue: <thin | copied | unlinked>
  Detail: <one sentence describing the specific problem>
  Suggested action: <expand summary | rewrite in own words | add cross-links>
  ```

## Protocol

1. Read `.review/state.yaml` to determine `last_review` date and prior scope.
   If the file is absent or `last_review` is null, treat this as the first run.
2. **Determine scope.** For the default `changed` scope, run:

   ```bash
   python3 .claude/skills/shared/review_scope.py <vault_root>
   ```

   (Use `python` on Windows, `python3` on macOS/Linux.)

   The script exits 0 and prints one path per line when pages are in scope,
   exits 1 when nothing has changed since last review (report "nothing new —
   skipping"), and exits 2 on error. The printed paths ARE the scope for steps 3–5.

   For `/review <topic-or-tag>`: pages matching that tag, or pages that link to
   the named topic page. Select them from the vault manually.

   For `/review --all`: all pages in `wiki/pages/`. Ask the user to confirm before
   proceeding — state the approximate page count.
3. Run Check A (contradictions) across all scoped page pairs that share named
   entities. Avoid O(n²) full cross-product: focus on entity clusters (pages
   sharing the same tag or linking to the same entity page).
4. Run Check B (faithfulness) on a sample of up to `max_faithfulness_pages`
   pages from the scope, prioritising pages updated most recently. For each
   sampled page, inspect up to 3 cited claims (the first 3 encountered, or
   those closest to the most recently updated content).
5. Run Check C (summary quality) across all scoped pages.
6. Write `.review/report.md` with findings grouped by check:
   ```markdown
   # Review Report — YYYY-MM-DD
   Scope: <scope description>
   Pages reviewed: N

   ## Contradictions
   (findings or "None found.")

   ## Claim↔Source Faithfulness
   Sampled: N pages
   (findings or "None found.")

   ## Summary Quality
   (findings or "None found.")
   ```
   Each finding includes severity (blocking / advisory), pages involved,
   claim text, source citation, and proposed action. **Never auto-apply.**
7. Update `.review/state.yaml`:
   ```yaml
   last_review: YYYY-MM-DD
   scope: changed|tag:<tag>|topic:<slug>|all
   findings_count: N
   last_exit_code: 0   # 0 = clean, 1 = findings, 2 = error
   ```
8. Append to `wiki/log.md` (Invariant #6):
   `## [YYYY-MM-DD] review | scope: <scope> | findings: N`
   `.review/report.md` is a runtime artifact — do not add it to `wiki/index.md`.
9. Suggest next actions based on findings:
   - Contradictions → "consider `/merge` to reconcile, or edit the claims manually"
   - Faithfulness failures → "consider `/refresh <source>` or editing the claim"
   - Summary quality → "consider expanding the summary or adding cross-links"

## Unattended mode

`/review` **is available unattended**: it reads pages and sources, writes
`.review/report.md` and `.review/state.yaml`, and updates `wiki/log.md`.
It never modifies `wiki/pages/`, `wiki/sources/`, or any other structural file.

## Output files

- `.review/report.md` — findings report (human-readable)
- `.review/state.yaml` — last-run metadata for scoping future runs
- `wiki/log.md` — append-only log entry (Invariant #6)
