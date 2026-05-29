#!/usr/bin/env python3
"""
fetch_inbox.py — Process inbox.md and populate raw/web/ (and raw/papers/ for PDFs).

Usage:
    python fetch_inbox.py                    # uses current dir as vault
    python fetch_inbox.py --vault /path      # explicit vault path
    python fetch_inbox.py --dry-run          # shows what would be done

Reads `inbox.md` from the vault root, finds unchecked URL entries,
fetches each, and writes clean markdown + images to raw/web/<slug>/.
PDFs go to raw/papers/<slug>/paper.pdf with a companion index.md.

Idempotent: already-processed URLs are skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, urljoin

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from vault_state import load_config, read_state, write_state
from console import ensure_utf8_stdout
ensure_utf8_stdout()

# --- Dependency check with friendly error -----------------------------------

MISSING_DEPS = []
try:
    import requests
except ImportError:
    MISSING_DEPS.append("requests")
try:
    import trafilatura
except ImportError:
    MISSING_DEPS.append("trafilatura")
try:
    from slugify import slugify
except ImportError:
    MISSING_DEPS.append("python-slugify")

if MISSING_DEPS:
    print("Missing dependencies. Install with:", file=sys.stderr)
    print(f"  pip install {' '.join(MISSING_DEPS)}", file=sys.stderr)
    sys.exit(1)


# --- Data types -------------------------------------------------------------

@dataclass
class InboxEntry:
    url: str
    line_index: int
    raw_line: str
    tags: list = field(default_factory=list)
    note: str | None = None


@dataclass
class FetchResult:
    url: str
    ok: bool
    kind: str  # "html" | "pdf" | "failed"
    out_path: Path | None = None
    reason: str | None = None


# --- Constants --------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (compatible; InboxFetcher/1.0; "
    "+https://github.com/anthropic/skills)"
)

UNCHECKED_PATTERN = re.compile(r"^- \[ \] (https?://\S+)\s*$")
# Matches an unchecked entry that was previously attempted but failed:
#   - [ ] https://example.com ⚠ reason text
# Used by --retry mode to select only failed entries for re-attempt.
FAILED_PATTERN = re.compile(r"^- \[ \] (https?://\S+) ⚠ .+$")
# Near-miss: looks like an unchecked entry but has trailing text after the URL.
# These are silently dropped by UNCHECKED_PATTERN; emit a visible warning instead.
_NEAR_MISS_PATTERN = re.compile(r"^- \[ \] https?://\S+\s+\S")
IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

PLAYWRIGHT_HINT = "try playwright"


def _should_propagate_tags(config: dict) -> bool:
    """Return True when inbox tag/note propagation is enabled (default: True)."""
    return bool(config.get("inbox", {}).get("tags_propagation", True))


# --- Core operations --------------------------------------------------------

def find_unchecked_entries(inbox_text: str) -> list[InboxEntry]:
    """Parse inbox.md and return unchecked URL entries with any tag/note hints."""
    stripped = re.sub(r"<!--.*?-->", "", inbox_text, flags=re.DOTALL)
    lines = stripped.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = UNCHECKED_PATTERN.match(line)
        if match:
            entry = InboxEntry(
                url=match.group(1).strip(),
                line_index=i,
                raw_line=line,
            )
            # Collect indented sub-bullets immediately following the URL line
            j = i + 1
            while j < len(lines):
                sub = lines[j]
                if not sub.startswith(" ") and not sub.startswith("\t"):
                    break
                sub_stripped = sub.strip()
                if sub_stripped.startswith("- tags:"):
                    raw_tags = sub_stripped[len("- tags:"):].strip()
                    entry.tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                elif sub_stripped.startswith("- note:"):
                    entry.note = sub_stripped[len("- note:"):].strip()
                j += 1
            entries.append(entry)
            i = j
        else:
            i += 1
    return entries


def find_failed_entries(inbox_text: str) -> list[InboxEntry]:
    """Parse inbox.md and return only previously-failed entries (⚠-marked).

    Picks up sub-bullets (tags/note) so retry context is preserved from
    the original fetch attempt.
    """
    stripped = re.sub(r"<!--.*?-->", "", inbox_text, flags=re.DOTALL)
    lines = stripped.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = FAILED_PATTERN.match(line)
        if match:
            entry = InboxEntry(
                url=match.group(1).strip(),
                line_index=i,
                raw_line=line,
            )
            # Collect indented sub-bullets (tags/note) that may follow.
            j = i + 1
            while j < len(lines):
                sub = lines[j]
                if not sub.startswith(" ") and not sub.startswith("\t"):
                    break
                sub_stripped = sub.strip()
                if sub_stripped.startswith("- tags:"):
                    raw_tags = sub_stripped[len("- tags:"):].strip()
                    entry.tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                elif sub_stripped.startswith("- note:"):
                    entry.note = sub_stripped[len("- note:"):].strip()
                j += 1
            entries.append(entry)
            i = j
        else:
            i += 1
    return entries


def is_pdf_url(url: str) -> bool:
    """Heuristic: URL path ends in .pdf."""
    return Path(urlparse(url).path).suffix.lower() == ".pdf"


def is_walled(url: str, walled: frozenset) -> bool:
    """Preflight check: URL host is in the walled-domain list."""
    host = urlparse(url).netloc.lower()
    return host in walled


def rewrite_url_for_fetch(url: str) -> tuple[str, str | None]:
    """Rewrite a user-supplied URL into a better fetch target.

    Returns (fetch_url, slug_override). When slug_override is non-None
    it is used as the raw-file slug verbatim (bypassing slugify) so
    canonical identifiers like arxiv paper IDs survive intact.

    Arxiv abstract and HTML URLs are rewritten to the PDF endpoint so
    we archive the paper itself instead of the landing page.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if host in ("arxiv.org", "export.arxiv.org"):
        m = re.match(r"^/(?:abs|html|pdf)/(.+?)(?:\.pdf)?$", parsed.path)
        if m:
            paper_id = m.group(1)
            slug = f"arxiv-{paper_id.replace('/', '-')}"
            return f"https://arxiv.org/pdf/{paper_id}.pdf", slug
    return url, None


def slug_from(url: str, title: str | None) -> str:
    """Generate a filesystem-safe slug, preferring the title."""
    if title and title.strip():
        s = slugify(title)[:80]
        if s:
            return s
    host = urlparse(url).netloc.replace("www.", "")
    h = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{slugify(host)}-{h}"


def fetch_pdf(url: str, papers_dir: Path,
              slug_override: str | None = None,
              pdf_timeout: int = 60,
              max_pdf_mb: int = 50,
              tags: list | None = None,
              note: str | None = None,
              propagate_tags: bool = True) -> FetchResult:
    """Download a PDF into a raw/papers/<slug>/ folder with a companion index.md."""
    try:
        r = requests.get(
            url,
            timeout=pdf_timeout,
            headers={"User-Agent": USER_AGENT},
            stream=True,
        )
        r.raise_for_status()
    except Exception as e:
        return FetchResult(url=url, ok=False, kind="failed",
                           reason=f"pdf download failed: {e}")

    size = int(r.headers.get("Content-Length", 0))
    max_bytes = max_pdf_mb * 1024 * 1024

    # Fail fast when the server declares the size upfront
    if size > max_bytes:
        return FetchResult(url=url, ok=False, kind="failed",
                           reason=f"PDF too large ({size // 1024 // 1024} MB > {max_pdf_mb} MB limit)")

    slug = slug_override or slug_from(url, None)
    out_dir = papers_dir / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_file = out_dir / "paper.pdf"

    # Stream to disk, abort and clean up if we exceed the limit mid-download
    # (handles servers that omit Content-Length)
    accumulated = 0
    overflow = False
    try:
        with open(pdf_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                accumulated += len(chunk)
                if accumulated > max_bytes:
                    overflow = True
                    break
                f.write(chunk)
    except Exception as e:
        pdf_file.unlink(missing_ok=True)
        try:
            out_dir.rmdir()
        except OSError:
            pass
        return FetchResult(url=url, ok=False, kind="failed",
                           reason=f"pdf download failed: {e}")

    if overflow:
        pdf_file.unlink(missing_ok=True)
        try:
            out_dir.rmdir()
        except OSError:
            pass
        return FetchResult(url=url, ok=False, kind="failed",
                           reason=f"PDF too large (exceeded {max_pdf_mb} MB mid-stream)")

    # Infer a human-readable title from the slug override
    if slug_override and slug_override.startswith("arxiv-"):
        arxiv_id = slug_override[len("arxiv-"):].replace("-", ".", 1)
        title = f"arxiv:{arxiv_id}"
    else:
        title = "Untitled"

    fm_lines = [
        "---",
        f"source_url: {url}",
        f"title: {yaml_escape(title)}",
        f"fetched: {date.today().isoformat()}",
        "fetch_method: pdf",
    ]
    if propagate_tags:
        if tags:
            fm_lines.append(f"tags: [{', '.join(tags)}]")
        if note:
            fm_lines.append(f"note: {yaml_escape(note)}")
    fm_lines += ["---", "", "PDF: [[paper.pdf]]", ""]

    (out_dir / "index.md").write_text("\n".join(fm_lines), encoding="utf-8")

    return FetchResult(url=url, ok=True, kind="pdf", out_path=out_dir)


def fetch_html(url: str, web_dir: Path, html_timeout: int = 20,
               tags: list | None = None, note: str | None = None,
               propagate_tags: bool = True) -> FetchResult:
    """Fetch an HTML article, extract clean markdown, download images."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return FetchResult(url=url, ok=False, kind="failed",
                           reason=f"fetch returned empty (network / 403 / paywall) — {PLAYWRIGHT_HINT}")

    result = trafilatura.extract(
        downloaded,
        output_format="markdown",
        with_metadata=True,
        include_images=True,
        include_links=True,
        include_tables=True,
    )
    if not result or not result.strip():
        return FetchResult(url=url, ok=False, kind="failed",
                           reason=f"extraction empty (likely paywall or JS-rendered) — {PLAYWRIGHT_HINT}")

    meta = trafilatura.extract_metadata(downloaded)
    title = getattr(meta, "title", None) if meta else None
    author = getattr(meta, "author", None) if meta else None
    pub_date = getattr(meta, "date", None) if meta else None
    language = getattr(meta, "language", None) if meta else None

    slug = slug_from(url, title)
    out_dir = web_dir / slug
    assets_dir = out_dir / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(exist_ok=True)

    md_with_local_images = download_images(result, assets_dir, base_url=url,
                                           html_timeout=html_timeout)

    frontmatter_lines = [
        "---",
        f"source_url: {url}",
        f"title: {yaml_escape(title) if title else 'Untitled'}",
    ]
    if author:
        frontmatter_lines.append(f"author: {yaml_escape(author)}")
    if pub_date:
        frontmatter_lines.append(f"published: {pub_date}")
    if language:
        frontmatter_lines.append(f"language: {language}")
    if propagate_tags:
        if tags:
            frontmatter_lines.append(f"tags: [{', '.join(tags)}]")
        if note:
            frontmatter_lines.append(f"note: {yaml_escape(note)}")
    frontmatter_lines.append(f"fetched: {date.today().isoformat()}")
    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines) + "\n\n"

    body = f"# {title or 'Untitled'}\n\n{md_with_local_images}\n"
    (out_dir / "index.md").write_text(frontmatter + body, encoding="utf-8")

    return FetchResult(url=url, ok=True, kind="html", out_path=out_dir)


def download_images(md: str, assets_dir: Path, base_url: str,
                    html_timeout: int = 20) -> str:
    """Download all images referenced in md, rewrite paths to local assets/."""

    def replace(match: re.Match) -> str:
        alt, src = match.group(1), match.group(2)
        # Resolve relative URLs against the page URL
        if not src.startswith(("http://", "https://")):
            src_abs = urljoin(base_url, src)
        else:
            src_abs = src
        try:
            r = requests.get(
                src_abs,
                timeout=html_timeout,
                headers={"User-Agent": USER_AGENT},
            )
            r.raise_for_status()
        except Exception:
            return match.group(0)  # keep original link on failure

        ext = Path(urlparse(src_abs).path).suffix or ".png"
        if len(ext) > 6:  # weird extension, fallback
            ext = ".png"
        name = hashlib.sha1(src_abs.encode()).hexdigest()[:12] + ext
        (assets_dir / name).write_bytes(r.content)
        return f"![{alt}](assets/{name})"

    return IMG_PATTERN.sub(replace, md)


def yaml_escape(s: str) -> str:
    """Minimal YAML string escape: quote if it contains special chars."""
    if any(c in s for c in ":#\"'\n"):
        return '"' + s.replace('"', '\\"').replace("\n", " ") + '"'
    return s


def get_content_type(url: str, timeout: int = 10) -> str:
    """Probe a URL with a HEAD request; return the Content-Type value or empty string."""
    try:
        r = requests.head(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        return r.headers.get("Content-Type", "")
    except Exception:
        return ""


# --- Inbox rewriting --------------------------------------------------------

def update_inbox(
    inbox_path: Path,
    inbox_text: str,
    results: list[FetchResult],
    processed_section: str = "## Processed",
) -> str:
    # Detect and preserve the original line separator
    line_sep = "\r\n" if "\r\n" in inbox_text else "\n"
    lines = inbox_text.splitlines()
    today = date.today().isoformat()

    result_by_url = {r.url: r for r in results}
    new_processed_lines: list[str] = []
    out_lines: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        match = UNCHECKED_PATTERN.match(line)
        failed_match = FAILED_PATTERN.match(line) if not match else None
        if not match and not failed_match:
            # Warn on near-miss: looks like an unchecked entry but URL is not alone.
            # Guard "⚠ skipped:" sentinel to stay idempotent across repeated runs.
            if _NEAR_MISS_PATTERN.match(line) and "⚠ skipped:" not in line:
                out_lines.append(
                    line + " ⚠ skipped: inline text after URL"
                    " — move notes to an indented sub-bullet"
                )
            else:
                out_lines.append(line)
            i += 1
            continue

        url = (match or failed_match).group(1).strip()

        # Determine the span of indented sub-bullets that follow this URL line
        j = i + 1
        while j < len(lines) and (
            lines[j].startswith(" ") or lines[j].startswith("\t")
        ):
            j += 1

        if url not in result_by_url:
            # Not in this batch — preserve URL and sub-bullets unchanged
            out_lines.extend(lines[i:j])
            i = j
            continue

        result = result_by_url[url]
        if result.ok:
            rel = result.out_path
            new_processed_lines.append(
                f"- [x] {url} → `{rel}` ({today})"
            )
            # Sub-bullets have been written to raw frontmatter; drop them here
        else:
            out_lines.append(f"- [ ] {url} ⚠ {result.reason}")
            # Keep sub-bullets under the failure line for retry context
            out_lines.extend(lines[i + 1:j])

        i = j

    final_lines = list(out_lines)
    if new_processed_lines:
        if not any(l.strip() == processed_section for l in final_lines):
            if final_lines and final_lines[-1].strip():
                final_lines.append("")
            final_lines.append(processed_section)
            final_lines.append("")
        final_lines.extend(new_processed_lines)

    ending = line_sep if inbox_text.endswith(("\n", "\r\n")) else ""
    return line_sep.join(final_lines) + ending


# --- Orchestration ----------------------------------------------------------

def process_vault(vault: Path, dry_run: bool = False, retry: bool = False) -> int:
    cfg = load_config(vault)
    processed_section = cfg["inbox"]["processed_section"]
    html_timeout = cfg["fetch"]["html_timeout_seconds"]
    pdf_timeout = cfg["fetch"]["pdf_timeout_seconds"]
    max_pdf_mb = cfg["fetch"]["max_pdf_size_mb"]
    pdf_enabled = cfg["fetch"]["pdf_enabled"]
    walled = frozenset(cfg["fetch"]["walled_domains"])
    propagate_tags = _should_propagate_tags(cfg)

    inbox_path = vault / "inbox.md"
    if not inbox_path.exists():
        print(f"ERROR: inbox.md not found at {inbox_path}", file=sys.stderr)
        return 1

    web_dir = vault / "raw" / "web"
    papers_dir = vault / "raw" / "papers"

    inbox_text = inbox_path.read_text(encoding="utf-8")
    entries = find_failed_entries(inbox_text) if retry else find_unchecked_entries(inbox_text)

    if not entries:
        mode_label = "No failed URLs" if retry else "Inbox empty"
        print(f"{mode_label}. Nothing to do.")
        return 0

    print(f"Found {len(entries)} URL(s) to process.")
    if dry_run:
        for e in entries:
            print(f"  would fetch: {e.url}")
        return 0

    results: list[FetchResult] = []
    for e in entries:
        fetch_url, slug_override = rewrite_url_for_fetch(e.url)
        if fetch_url != e.url:
            print(f"\n→ {e.url}\n  (fetching as → {fetch_url})")
        else:
            print(f"\n→ {e.url}")

        if is_pdf_url(fetch_url):
            if not pdf_enabled:
                r = FetchResult(
                    url=fetch_url, ok=False, kind="failed",
                    reason="PDF fetch disabled (pdf_enabled: false in vault.config.yml)",
                )
            else:
                r = fetch_pdf(fetch_url, papers_dir, slug_override=slug_override,
                              pdf_timeout=pdf_timeout, max_pdf_mb=max_pdf_mb,
                              tags=e.tags, note=e.note,
                              propagate_tags=propagate_tags)
        elif is_walled(fetch_url, walled):
            host = urlparse(fetch_url).netloc.lower()
            r = FetchResult(
                url=fetch_url, ok=False, kind="failed",
                reason=f"walled domain ({host}) — {PLAYWRIGHT_HINT}",
            )
        elif "application/pdf" in get_content_type(fetch_url):
            if not pdf_enabled:
                r = FetchResult(
                    url=fetch_url, ok=False, kind="failed",
                    reason="PDF fetch disabled (pdf_enabled: false in vault.config.yml)",
                )
            else:
                r = fetch_pdf(fetch_url, papers_dir, slug_override=slug_override,
                              pdf_timeout=pdf_timeout, max_pdf_mb=max_pdf_mb,
                              tags=e.tags, note=e.note,
                              propagate_tags=propagate_tags)
        else:
            r = fetch_html(fetch_url, web_dir, html_timeout=html_timeout,
                           tags=e.tags, note=e.note,
                           propagate_tags=propagate_tags)

        # Track by the original inbox URL, not the rewritten fetch URL,
        # so update_inbox can match the line back.
        r.url = e.url
        results.append(r)
        if r.ok:
            print(f"  ✓ {r.kind} → {r.out_path}")
        else:
            print(f"  ⚠ {r.reason}")

    new_text = update_inbox(inbox_path, inbox_text, results,
                            processed_section=processed_section)
    inbox_path.write_text(new_text, encoding="utf-8")

    # Summary
    n_html = sum(1 for r in results if r.ok and r.kind == "html")
    n_pdf = sum(1 for r in results if r.ok and r.kind == "pdf")
    n_fail = sum(1 for r in results if not r.ok)
    print()
    print(f"Processed {len(results)} URLs:")
    print(f"  ✓ {n_html} HTML article(s) → raw/web/")
    print(f"  ✓ {n_pdf} PDF(s) → raw/papers/")
    if n_fail:
        print(f"  ⚠ {n_fail} failed (see inbox.md for reasons)")

    if n_html + n_pdf > 0:
        state = read_state(vault)
        prev = int(state.get("fetches_since_last_lint", 0))
        write_state(vault, {"fetches_since_last_lint": prev + 1})

    return 0 if n_fail == 0 else 2  # 2 = partial success


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch URLs from inbox.md into raw/ as markdown."
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=Path.cwd(),
        help="Path to vault root (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List URLs that would be fetched, don't download.",
    )
    parser.add_argument(
        "--retry",
        action="store_true",
        help="Re-attempt only previously-failed (⚠-marked) inbox entries.",
    )
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    if not vault.is_dir():
        print(f"ERROR: vault path is not a directory: {vault}",
              file=sys.stderr)
        return 1

    return process_vault(vault, dry_run=args.dry_run, retry=args.retry)


if __name__ == "__main__":
    sys.exit(main())
