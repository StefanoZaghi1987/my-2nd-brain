---
description: Write or update wiki/hot.md with a brief record of what was covered
  this session, what's still open, and what to pick up next. Run at session end
  after any wiki/ writes. Replaces the previous entry — never appends.
---

# /hot — Update the session hot cache

## When to use

At the end of any session in which wiki/ was written to (ingest, promote,
view, forget, reflect, refresh). Also useful mid-session to checkpoint state.

The user can call this explicitly. The agent should call it automatically
before giving its final response in a writing session.

## What to write

5–10 lines covering three things:

1. **What we did** — sources ingested, pages touched, views built,
   decisions made (slug names, tag choices, structural calls).
2. **What's open** — any ⚠ linter findings not resolved, deferred
   decisions, unfinished trains of thought.
3. **What to pick up next** — the single most useful thing to do
   next session, stated concretely.

## Format

```markdown
## [YYYY-MM-DD]

[5-10 lines of prose or bullets — no headers inside]
```

Replace the entire file. Do not append. The hot cache is a snapshot,
not a log (`wiki/log.md` is the append-only record).
