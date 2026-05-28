---
description: Retrieve walled, paywalled, or JS-rendered URLs that the inbox
  fetcher could not download. Uses the Playwright MCP browser interactively,
  one URL at a time, with user confirmation per URL. Run after /fetch leaves
  ⚠ try playwright markers in inbox.md.
---

# /playwright-fetch — Retrieve URLs via browser

## When to use

After `/fetch`, when inbox.md contains lines marked:
```
- [ ] https://example.com/article ⚠ walled domain — try playwright
- [ ] https://paywall.com/piece ⚠ extraction empty — try playwright
```

## One URL at a time

Never batch-process walled URLs unattended. Each URL requires:
1. Confirm with the user before navigating.
2. Navigate with `browser_navigate`.
3. If auth is required: stop and report — do not attempt to bypass.
4. Extract content with `browser_snapshot` (accessibility tree) or
   `browser_evaluate` (DOM extraction). For X/Twitter threads: collect
   the full thread, not just the root post.

## Writing the output

For each successfully retrieved URL, write `raw/web/<slug>/index.md`:

```yaml
---
source_url: <url>
title: <inferred or first line>
author: <handle or author name>
published: <YYYY-MM-DD if visible>
fetched: <today>
fetched_via: playwright
---
```

Slug: prefer article title; for X/Twitter use `<handle>-<tweet-id>`.

Save screenshots to `raw/web/<slug>/assets/` only if the user asks.

## Inbox update

For each success, update inbox.md: move the line to `## Processed`
with `- [x] <url> → \`raw/web/<slug>/\` (<today>)`. Remove the ⚠ marker.

For each failure, keep the line unchecked. Append the failure reason
after ⚠ and ask the user how to proceed.

## After

When all ⚠ URLs have been attempted, report outcomes and offer `/ingest`
on the newly written files.

## Out of scope

- Bypassing login walls or solving CAPTCHAs.
- Batch processing (every URL needs a confirmation).
- Any URL not already marked ⚠ by `/fetch`.
