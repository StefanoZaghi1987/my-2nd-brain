---
description: Re-fetch a source whose content has changed and re-ingest it,
  preserving the citation graph. Flags potentially changed claims in wiki/pages/
  with a needs-review frontmatter tag for user review. Does not rewrite prose.
---

# /refresh — Refresh a source

Update a source that has changed since it was ingested, without losing
the pages and views built on top of it.

## Arguments

`/refresh <source>` where `<source>` can be:

- A slug: `/refresh agent-skills-spec`
- A wiki path: `/refresh wiki/sources/agent-skills-spec.md`
- A raw path: `/refresh raw/web/agent-skills-spec/index.md`
- A URL (agent resolves to slug)

## Protocol

1. **Resolve slug.** Find `wiki/sources/<slug>.md` and read `source_url`
   and `fetch_method` from its frontmatter. Confirm with the user:
   show title, source_url, and fetch_method.

2. **Branch by source type.**

   **Web article** (`fetch_method` absent or `html`):
   Add the URL back to `inbox.md` as an unchecked entry under "To process"
   (`inbox.md` is not under `raw/` — this write is permitted by invariant #1):
   ```
   - [ ] <source_url>
   ```
   Instruct the user to run the fetcher to overwrite the raw folder:
   ```bash
   python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
   ```
   Wait for the fetcher to complete before proceeding to step 3.

   **PDF source** (`fetch_method: pdf`):
   Ask the user: "This is a PDF source — PDFs rarely change. Re-fetch
   the file from the original URL, or re-summarise from the existing
   `raw/papers/<slug>/paper.pdf`?"
   - **Re-fetch:** add URL to `inbox.md` and proceed as the web article
     branch above.
   - **Re-summarise:** skip to step 3 directly, using the existing
     `paper.pdf`.

3. **Re-ingest.** Rewrite `wiki/sources/<slug>.md` with an updated
   summary. Bump `updated` to today.

4. **Flag affected pages.** Scan `wiki/pages/` for files that cite this source.
   For each affected page, add `needs-review` to its `tags` frontmatter list:
   ```yaml
   tags: [needs-review]
   ```
   List every flagged page in the final report.

5. **Update log.** Append to `wiki/log.md`:
   `## [YYYY-MM-DD] refresh | <slug>`

## What /refresh does NOT do

- Does not rewrite page prose automatically — step 4 flags only.
- Does not delete or recreate the source entry — identity (slug) is preserved.
- Does not cascade through views — re-run /lint after refresh to check
  view staleness.

## Rules

- Confirm the resolved slug and URL with the user before queuing the re-fetch.
- If more than 15 pages cite the source (invariant #5), report the fanout
  and let the user decide scope.
- `/refresh` requires interactive mode. The re-fetch (step 2) requires the user
  to run the fetcher script, which cannot be invoked in unattended mode. Steps 3–5
  may proceed once the raw folder has been refreshed in a prior interactive session,
  but the command as a whole is not safe to run unattended from step 1.
