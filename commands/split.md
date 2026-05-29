---
description: Split an overgrown wiki page into two focused ones, rewriting all
  backlinks so the vault stays consistent. Interactive — never available in
  unattended mode. Triggered by lint duplicate findings or when a single page
  has grown to cover too many distinct concepts.
---

# /split — Split a wiki page into two

Break an overgrown page into two focused ones. Rewrites all backlinks so the
vault stays consistent. Typically triggered by a lint duplicate finding or when
a page has grown to cover too many distinct concepts.

## Arguments

`/split <page> <new-page-A> <new-page-B>` where `<page>` is the original page
to dissolve and the two new slugs name the resulting pages.

- `/split agent-tools agent-tools-builtin agent-tools-custom`

If the target slugs are not supplied, ask the user before proceeding.

> **Merging two pages instead?** See [`/merge`](.claude/commands/merge.md) — it has its
> own protocol for consolidating near-duplicate pages.

---

## SPLIT Protocol

### 1. Identify

User provides the page to split and names the two new target pages.
Resolve the original page to an absolute wiki path. Confirm with the
user: show the page title and the two new slugs.

### 2. Show content and assign sections

Read the original page in full and display it. Ask the user to mark
which sections (or claims) go to which new target page. If any section
is ambiguous, ask explicitly rather than guessing.

Wait for the user to confirm the full assignment before proceeding.

### 3. Check backlink fanout

Run `.claude/skills/shared/find_backlinks.py` against the original page
before writing anything:

```
python3 .claude/skills/shared/find_backlinks.py <vault_root> <path-to-original-page>
```

(Use `python` on Windows, `python3` on macOS/Linux.)

List every file returned. If the fanout exceeds **15 files** — stop
immediately. Report the complete file list and do not proceed. Let the
user choose to continue across multiple passes or stop entirely.

See the Guards section for the full fanout protocol.

### 4. Write two new pages

Write `wiki/pages/<new-page-A>.md` and `wiki/pages/<new-page-B>.md`
with the content assigned in step 2. Apply standard wiki frontmatter
to each. Set `created` and `updated` to today's date for both new
pages. Do not copy claims that belong to the other new page.

### 5. Rewrite backlinks

For each file in the backlink list from step 3, **excluding the
original page itself** (it will be deleted in step 6):

- If the context of the link clearly belongs to one of the two new
  pages (e.g., the surrounding text refers to content that went to
  new-page-A), rewrite the link to that page.
- If the context is ambiguous, ask the user per-link before rewriting.
- If the user chooses neither new page, leave the link unchanged and
  flag it in the final report as requiring manual resolution after
  the split.

Apply the same four-form rewriting rule as in `/merge` step 7 — all link
variants in a given file must be rewritten in one pass:

- Bare slug: `[[page]]` → `[[new-page-A]]` or `[[new-page-B]]`
- Vault-relative without extension: `[[wiki/pages/page]]` → `[[wiki/pages/new-page-A]]`
- With `.md` extension: `[[wiki/pages/page.md]]` → `[[wiki/pages/new-page-A.md]]`
- Aliased form: `[[wiki/pages/page|Display Text]]` → `[[wiki/pages/new-page-A|Display Text]]`

### 6. Delete the original page

Delete `wiki/pages/<original-page>.md` once all backlinks have been
confirmed rewritten.

### 7. Update bookkeeping

- `wiki/index.md`: remove the original page entry; add entries for
  both new pages.
- `wiki/log.md`: append one line:
  `## [YYYY-MM-DD] split <original-page> → <new-page-A>, <new-page-B>`
  with a count of files rewritten.

Propose running `/lint` to confirm no dead links remain.

---

## Guards

**Fanout guard (>15 files):** If `find_backlinks.py` returns more than
15 files, stop immediately. Report the complete file list with counts.
Do not proceed until the user has either picked a subset of files to
rewrite in this pass or explicitly asked to continue across multiple
passes. Never silently exceed invariant #5.

**Prose-deletion guard:** Never delete content from the original page
without the user's approval. Show all assignments in step 2, wait for
explicit confirmation before writing anything.

**Shareable view guard:** For any view in the backlink list with
`shareable: true`, do NOT rewrite the link. Warn the user that the
view still references the deleted original page and let them decide
whether to issue a new dated version.

**Confirm before delete:** Do not delete the original page (step 6)
until all backlink rewrites have been applied and confirmed. Deletion is
irreversible.

## Unattended mode

`/split` is **not available unattended**. The operation involves
irreversible deletions and per-claim assignment decisions that require
the user in the loop. If invoked unattended, refuse with a clear
message and suggest running the command interactively.

## Report format

End of SPLIT operation, tell the user:

```
Split: <original-page> → <new-page-A>, <new-page-B>
  ✓ Wrote: wiki/pages/<new-page-A>.md
  ✓ Wrote: wiki/pages/<new-page-B>.md
  ✓ Rewrote backlinks in N pages
  ⚠ N links left ambiguous (flagged in report above)
  ⚠ N shareable views left as-is (still reference deleted page)
  ✓ Deleted: wiki/pages/<original-page>.md
```
