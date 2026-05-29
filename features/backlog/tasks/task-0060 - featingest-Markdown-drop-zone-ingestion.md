---
id: TASK-0060
title: 'feat(ingest): Markdown drop-zone ingestion'
status: To Do
assignee: []
created_date: '2026-05-29 06:56'
labels:
  - ingest
  - drop-zone
  - markdown
dependencies: []
documentation:
  - features/specs/2026-05-29-markdown-drop-ingest-design.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Allow users to drop `.md` files into `raw/drop/` alongside PDFs, run `/ingest`, and have them automatically adopted into `raw/local/<slug>/` and ingested into the wiki.

**Design decisions (from spec):**
- Same `raw/drop/` folder for all file types; `adopt_drop.py` routes by extension via a type-handler registry
- `adopt_md()` writes `raw/local/<slug>/content.md` (original file, untouched) + `index.md` stub (fetch_method: local-md, extracted title/source_url)
- Title resolved by cascade: frontmatter `title:` → first `# H1` → filename stem
- `source_url` extracted from frontmatter keys: `source_url`, `url`, `link`, `source`
- Original file moved via `Path.rename()` (atomic, mirrors `adopt_pdf`)
- New `local-md` ingest branch reads `content.md` in full (no page limit)
- `check_drop_zone` linter check updated to count `.md` files alongside `.pdf`

**Spec:** `features/specs/2026-05-29-markdown-drop-ingest-design.md`
<!-- SECTION:DESCRIPTION:END -->
