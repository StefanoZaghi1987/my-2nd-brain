---
description: Process the URL queue in inbox.md. Downloads web articles and PDFs
  into raw/, marks successful fetches as done, and leaves failed URLs with ⚠ markers
  for Playwright fallback. Run before /ingest.
---

# /fetch — Process the inbox

## When to use

When inbox.md has unchecked URLs (`- [ ]`) and you want to download them.
Triggered by: "process the inbox", "fetch the URLs", "download these articles".

Always run /fetch before /ingest — ingest needs raw/ files to summarise.

## How to run

> **Windows:** replace `python3` with `python` in all commands below.

```bash
python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
```

Or dry-run to preview without writing:
```bash
python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --dry-run
```

## After running

1. Report the summary (✓ HTML, ✓ PDF, ⚠ failed counts).
2. For any `⚠ ... — try playwright` URLs, offer to run `/playwright-fetch`
   to retrieve them interactively via the browser.
3. When there are no remaining ⚠ markers (or the user skips Playwright),
   offer to run `/ingest` on the newly downloaded files.
