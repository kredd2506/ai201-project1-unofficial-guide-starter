"""
Stage 1 of the RAG pipeline: ingestion.

Fetches the 17 NRP.ai user-doc pages (see the Documents table in planning.md),
saves the raw HTML for reproducibility, then extracts the substantive content
and writes clean Markdown into documents/.

Markdown is the chosen intermediate format because the chunking strategy
(chunk.py) is structure-aware: headings -> `#` and code blocks -> fenced
``` blocks give chunk.py the section/code boundaries it splits on.

What gets kept vs. removed
  KEEP: the page body (div.sl-markdown-content) — prose, lists, tables, and
        the Starlight callouts/asides (e.g. "Required", "containers are
        stateless"), which hold key facts.
  REMOVE: site nav, header, footer, the right-sidebar table of contents,
          callout icon SVGs, and buttons.

Run:  python ingest.py
"""

import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

# (slug, page title is read from the page itself, url) — slugs match planning.md.
SOURCES = [
    ("getting-started",      "https://nrp.ai/documentation/userdocs/start/getting-started"),
    ("using-nautilus",       "https://nrp.ai/documentation/userdocs/start/using-nautilus"),
    ("policies",             "https://nrp.ai/documentation/userdocs/start/policies"),
    ("faq",                  "https://nrp.ai/documentation/userdocs/start/faq"),
    ("glossary",             "https://nrp.ai/documentation/userdocs/start/glossary"),
    ("support",              "https://nrp.ai/documentation/userdocs/start/support"),
    ("gpu-pods",             "https://nrp.ai/documentation/userdocs/running/gpu-pods"),
    ("jobs",                 "https://nrp.ai/documentation/userdocs/running/jobs"),
    ("storage-intro",        "https://nrp.ai/documentation/userdocs/storage/intro"),
    ("storage-ceph",         "https://nrp.ai/documentation/userdocs/storage/ceph"),
    ("move-data",            "https://nrp.ai/documentation/userdocs/storage/move-data"),
    ("llm-managed",          "https://nrp.ai/documentation/userdocs/ai/llm-managed"),
    ("tutorial-introduction","https://nrp.ai/documentation/userdocs/tutorial/introduction"),
    ("tutorial-basic",       "https://nrp.ai/documentation/userdocs/tutorial/basic"),
    ("tutorial-docker",      "https://nrp.ai/documentation/userdocs/tutorial/docker"),
    ("tutorial-debugging",   "https://nrp.ai/documentation/userdocs/tutorial/debugging"),
    ("jupyter-pod",          "https://nrp.ai/documentation/userdocs/jupyter/jupyter-pod"),
]

DOCS_DIR = Path("documents")
RAW_DIR = DOCS_DIR / "raw"
HEADERS = {"User-Agent": "Mozilla/5.0 (RAG course project; ingestion script)"}


class NRPConverter(MarkdownConverter):
    """Emit fenced code blocks tagged with the page's data-language attribute."""

    def convert_img(self, el, text, parent_tags=None):
        # Drop images: this is a text RAG corpus and the doc images carry no
        # alt text, so `![](...)` links are noise.
        alt = el.get("alt", "").strip()
        return alt

    def convert_pre(self, el, text, parent_tags=None):
        lang = el.get("data-language", "") or ""
        # Starlight's Expressive Code renderer puts each source line in its own
        # <div class="ec-line"> with no newline text between them, so a plain
        # get_text() collapses multi-line blocks (e.g. YAML pod specs) onto one
        # line. Join the per-line divs to restore the original line breaks.
        ec_lines = el.select("div.ec-line")
        code = "\n".join(ln.get_text() for ln in ec_lines) if ec_lines else el.get_text()
        return f"\n\n```{lang}\n{code}\n```\n\n"


def fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def clean_to_markdown(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1")
    title = title.get_text(strip=True) if title else url.rstrip("/").split("/")[-1]

    main = soup.select_one("div.sl-markdown-content")
    if main is None:
        raise ValueError(f"no content container (div.sl-markdown-content) found for {url}")

    # Normalize Starlight asides/callouts: the visible title <p> is just an icon
    # SVG; the real label lives in aria-label. Replace it with a bold heading so
    # the callout reads as a standalone note and doesn't fuse into nearby text.
    for aside in main.select("aside.starlight-aside"):
        label = aside.get("aria-label", "").strip()
        title_p = aside.select_one(".starlight-aside__title")
        if title_p:
            title_p.clear()
            if label:
                title_p.string = f"Note — {label}:"

    # Drop anything non-substantive that may sit inside the content div.
    # figcaption/sr-only = Expressive Code's code-block frame chrome (the
    # repeated "Terminal window" label and screen-reader-only text).
    for junk in main.select("svg, button, nav, aside.right-sidebar-container, figcaption, span.sr-only"):
        junk.decompose()

    md = NRPConverter(
        heading_style="ATX",
        bullets="-",
        escape_asterisks=False,
        escape_underscores=False,
        escape_misc=False,
    ).convert_soup(main)

    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return f"# {title}\n\nSource: {url}\n\n{md}\n"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ingesting {len(SOURCES)} pages -> {DOCS_DIR}/\n")
    rows = []
    for slug, url in SOURCES:
        try:
            html = fetch(url)
            (RAW_DIR / f"{slug}.html").write_text(html, encoding="utf-8")
            md = clean_to_markdown(html, url)
            (DOCS_DIR / f"{slug}.md").write_text(md, encoding="utf-8")
            rows.append((slug, len(md), "ok"))
            print(f"  ok   {slug:<24} {len(md):>7,} chars")
        except Exception as e:  # keep going; report at the end
            rows.append((slug, 0, f"FAIL: {e}"))
            print(f"  FAIL {slug:<24} {e}")
        time.sleep(0.5)  # be polite to the server

    ok = sum(1 for _, _, s in rows if s == "ok")
    print(f"\nDone: {ok}/{len(SOURCES)} pages written to {DOCS_DIR}/")
    if ok < len(SOURCES):
        print("Some pages failed — see FAIL rows above.")


if __name__ == "__main__":
    main()
