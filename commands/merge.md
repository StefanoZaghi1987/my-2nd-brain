---
description: Merge two near-duplicate wiki pages into one canonical page (rewriting all backlinks). Used to resolve lint duplicates and /review contradictions. Interactive — never available in unattended mode. For splitting a page, see /split.
---

# /merge — Merge wiki pages

Consolidate two near-duplicate pages into one canonical page. Rewrites
all backlinks so the vault stays consistent. Triggered by a duplicate
finding from `/lint` or a contradiction finding from `/review`.

## Arguments

`/merge <page-A> <page-B>` where page-A is the page to be merged away
and page-B is the canonical target that survives.

- Slugs: `/merge agent-tools agent-skills`
- Wiki paths: `/merge wiki/pages/agent-tools.md wiki/pages/agent-skills.md`
- If invoked from a `/review` contradiction finding, both pages are
  pre-populated — confirm before proceeding.

> **Splitting a page?** See [`/split`](.claude/commands/split.md) — it has its
> own protocol for breaking an overgrown page into two focused ones.

---

## MERGE Protocol

### 1. Identify

User provides page-A (to be merged away) and page-B (the canonical
target that survives). Resolve both to absolute wiki paths. Confirm
with the user: show both titles and the merge direction
(`page-A → page-B`).

If invoked from a `/review` contradiction finding, both pages are
pre-populated from the report. Still confirm the direction with the
user before proceeding.

### 2. Show content diff

Read both pages in full. Produce a diff-style summary that shows:

- **Overlapping content** — sections or claims present in both.
- **Unique to page-A** — content that will need to be merged in.
- **Unique to page-B** — content that would be unchanged.

Present this summary to the user and ask:

1. Confirm merge direction (page-A → page-B, or reverse).
2. Which content to keep when sections overlap.
3. Whether the final page should keep page-B's title or adopt a new one.

Wait for explicit confirmation before proceeding.

### 3. Confirm with user

Do not proceed until the user has approved the merge direction, content
decisions, and final title from step 2. Record any title change — if
the merged page adopts a new slug, note it now.

### 4. Check backlink fanout

Run `.claude/skills/shared/find_backlinks.py` against page-A:

```
python .claude/skills/shared/find_backlinks.py <vault_root> <path-to-page-A>
```

If a new slug C was chosen in Step 3, also run `find_backlinks.py`
against page-B and take the **union** of both result sets. The union
is the full set of files that need rewriting (links to either source
must be updated to point to C). The fanout guard applies to the
union count.

List every file returned, grouped by type:

```
wiki/pages/   (4 files link to page-A)
  - agent-orchestration.md: links here
  - context-engineering.md: links here
  - tool-use.md: links here
  - memory-patterns.md: links here
wiki/views/   (1 view links to page-A)
  - timeline-agent-capabilities.md (shareable: false)
```

If the fanout exceeds **15 files** — stop immediately. Report the
complete list and do not proceed. Let the user choose: run the merge
across multiple passes (picking a subset of files to rewrite per
pass), or stop entirely and handle it manually.

### 5. Draft merged content

Compose the merged page content, incorporating the decisions from
step 3. Apply the content choices the user approved. Show the full
draft to the user and ask for approval.

Do not write any files until the user has approved the draft.

### 6. Write the merged page

Write the approved content to page-B (or to a new slug if the title
changed in step 3). Use the standard wiki frontmatter. Update the
`updated` date. Preserve page-B's existing `created` date if writing
to the same slug. If writing to a new slug, set `created` to today.

If page-B was renamed to a new slug, the new file must go to
`wiki/pages/<new-slug>.md`. Note the new path — it will be the
rewrite target in step 7.

### 7. Rewrite all backlinks

For each file in the backlink list from step 4, **excluding page-A
itself** (it will be deleted in step 8 — do not rewrite it), replace
every link variant that resolved to page-A with the equivalent link
to page-B. All four link forms must be rewritten — not just one:

- Bare slug: `[[page-A]]` → `[[page-B]]`
- Vault-relative without extension: `[[wiki/pages/page-A]]` → `[[wiki/pages/page-B]]`
- With `.md` extension: `[[wiki/pages/page-A.md]]` → `[[wiki/pages/page-B.md]]`
- Aliased form: `[[wiki/pages/page-A|Display Text]]` → `[[wiki/pages/page-B|Display Text]]`
  (preserve the display label; swap only the target part)

If a new slug C was chosen in Step 3: rewrite links to page-A → C
**and** links to page-B → C, working across the full union of
backlink sets from Step 4. Exclude **both** page-A and page-B
themselves from the rewrite — they will both be deleted in Step 8
and must not be touched. Apply the same four-form rewriting rule for
each source slug.

A file that contains the same target in multiple forms must have all
forms rewritten in a single pass. After rewriting, confirm each file
to the user in the final report.

### 8. Delete page-A

Delete `wiki/pages/page-A.md`. This completes the merge by removing
the now-redundant source page. If a new slug C was chosen in Step 3,
delete **both** `wiki/pages/page-A.md` and `wiki/pages/page-B.md` —
page-B is also superseded and must not be left as an orphan. If
writing to page-B's existing slug, delete only page-A.

### 9. Update bookkeeping

- `wiki/index.md`: remove the page-A entry; update or add the page-B
  entry (reflecting any title change from step 3). If the merged page
  has a new slug (step 6), remove both the page-A entry and the old
  page-B entry from `wiki/index.md`, and add a single new entry for
  the merged page.
- `wiki/log.md`: append one line:
  `## [YYYY-MM-DD] merge <page-A> → <page-B>` with a count of files
  rewritten and whether any views were affected.

### 10. Propose lint

Propose running `/lint` to confirm zero dead links remain. Do not
run it automatically — let the user decide.

---

## Guards

**Fanout guard (>15 files):** If `find_backlinks.py` returns more than
15 files, stop immediately. Report the complete file list with counts.
Do not proceed until the user has either picked a subset of files to
rewrite in this pass or explicitly asked to continue across multiple
passes. Never silently exceed invariant #5.

**Prose-deletion guard:** Never delete content from a surviving page
without the user's approval. Draft first (step 5), show the draft,
wait for explicit confirmation.

**Shareable view guard:** For any view in the backlink list with
`shareable: true`, do NOT rewrite the link. Warn the user that the
view is now partially unsourced (it still references the deleted
page-A) and let them decide whether to issue a new dated version.

**Confirm before delete:** Do not delete page-A (step 8) until all
backlink rewrites have been applied and confirmed. Deletion is
irreversible.

## Unattended mode

`/merge` is **not available unattended**. The operation involves
irreversible deletions and per-claim decisions that require the user
in the loop. If invoked unattended, refuse with a clear message and
suggest running the command interactively.

## Report format

End of MERGE operation, tell the user:

```
Merged: <page-A> → <page-B>
  ✓ Wrote merged page: wiki/pages/<page-B>.md
  ✓ Rewrote backlinks in 4 pages
  ✓ Rewrote backlinks in 1 evolving view
  ⚠ 1 shareable view left as-is (still references deleted page-A)
  ✓ Deleted wiki/pages/<page-A>.md
  ✓ Updated wiki/index.md and wiki/log.md
  → Run /lint to confirm zero dead links
```
