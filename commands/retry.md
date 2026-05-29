---
description: Retry previously-failed inbox URLs. Finds unchecked entries
  marked with ⚠, re-attempts each, and clears the ⚠ marker on success.
  Successful retries are moved to the Processed section; persistent failures
  keep the ⚠ marker with a fresh reason. Does not touch plain unchecked
  entries or already-processed entries.
---

# /retry — Retry failed inbox URLs

## When to use

After `/fetch` marks some URLs with `⚠ reason` — for example after a transient
network error, a temporary server outage, or after adding authentication — when
you want to re-attempt only those specific URLs.

Untouched unchecked entries (`- [ ] url`) and already-processed entries (`[x]`)
are never touched by `/retry`.

## How to run

> **Windows:** replace `python3` with `python` in all commands below.

```bash
python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --retry
```

Or dry-run to preview which failed URLs would be retried:

```bash
python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --retry --dry-run
```

## After running

1. Report the retry summary (✓ cleared, ⚠ still failing counts).
2. For any `⚠ ... — try playwright` URLs, offer to run `/playwright-fetch`
   to retrieve them via the browser.
3. When retried items succeed, offer to run `/ingest` on the newly
   downloaded files.

## What /retry does NOT do

- Does not touch plain unchecked entries (`- [ ] url` without ⚠).
- Does not re-download already-processed (`[x]`) entries.
- Does not bypass walled-domain or PDF-disabled restrictions — those
  failures persist until the user acts on them (Playwright, config change).
