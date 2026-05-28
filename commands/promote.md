---
description: Promote insights from a saved conversation into wiki pages.
  Creates a wiki/sources/conv-<slug>.md entry making the conversation a
  first-class citable source. Interactive only — not available unattended.
---

# /promote — Promote conversation insights to wiki pages

Turn the synthesis in a saved conversation into citable wiki content.

## Arguments

`/promote [conversation-slug] [target-page]`

Both arguments are optional:
- No slug → operates on the most recent file in `conversations/`
- No target page → agent proposes candidate pages based on conversation content

## Protocol

1. **Read the conversation file.** Identify substantive synthesis claims —
   not questions, not summaries of external sources, but the user's own
   synthesised understanding.

2. **Identify the target page.** If given, use it. If not, propose 1–3
   candidate pages from `wiki/pages/` whose topics align with the claims.
   Ask the user to pick one before proceeding.

3. **Present candidate claims one by one.** For each claim:
   > "Claim: [claim text]. Add to [[wiki/pages/<target>]]?"
   Never write without explicit per-claim confirmation.

4. **Create `wiki/sources/conv-<slug>.md`** (if not already created):
   ```yaml
   ---
   type: source
   source_path: conversations/<slug>.md
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   tags: []
   ---
   # conv-<slug>
   
   One-line summary of what was promoted from this conversation.
   ```

5. **For each confirmed claim:** append it to `wiki/pages/<target>.md`
   with a citation: `[[wiki/sources/conv-<slug>]]`.
   `/promote` targets one wiki page per run. Run it again for a second target page.

6. **Update the conversation file frontmatter** — add or append to `promoted_to`:
   ```yaml
   promoted_to:
     - wiki/pages/<target>.md (YYYY-MM-DD)
   ```

7. **Update `wiki/index.md`** — add the new source entry under Sources.

8. **Append to `wiki/log.md`**: `## [YYYY-MM-DD] promote | conv-<slug> → <target>`

## Rules

- Never write a claim without per-claim user confirmation.
- Never create more than 3 new pages in a single /promote run (invariant #5).
- If the conversation has no substantive synthesis claims, say so and stop.
- Not available in unattended mode.

## What /promote does NOT do

- Does not rewrite the conversation file beyond the `promoted_to` frontmatter.
- Does not modify `raw/` in any way.
- Does not auto-create wiki pages — target page must already exist or be
  explicitly confirmed as new.
