"""
Stage 2 of the RAG pipeline: chunking.

Implements the structure-aware splitter from planning.md (Chunking Strategy):

  Primary split is STRUCTURAL — one chunk = one idea:
    - guides            -> split on Markdown headers (any level)
    - FAQ               -> split on `---` (one Q&A per chunk)
    - glossary          -> split per `- **Term**` bullet (one term per chunk)

  Recursive SIZE CAP:
    - guide sections over MAX_TOKENS (800) are sub-split on paragraph
      boundaries; a fenced ``` code block is treated as one unsplittable
      paragraph so commands/YAML are never cut (Anticipated Challenge #1).

  OVERLAP (1-2 sentences, ~120 tok):
    - added ONLY between sub-splits of the same oversized section.
    - NEVER added between independent FAQ/glossary entries (overlapping
      unrelated entries just adds noise).

Token counts use the BERT WordPiece tokenizer, which is identical for both
bge-small and nomic-embed (the embedding model) — so these counts match what
the embedder sees.

Output: chunks.jsonl, one JSON record per line:
  {id, doc, type, section, source_url, token_count, text}

Run:  python chunking.py
"""

import glob
import json
import re
from pathlib import Path

from transformers import AutoTokenizer

# --- size targets (tokens), from planning.md Chunking Strategy ---
MAX_TOKENS = 800          # hard cap for a guide chunk; trigger to sub-split
MIN_TOKENS = 500          # soft target floor for guide sections (not enforced;
                          # structural sections below this are kept as-is)
ATOMIC_MIN, ATOMIC_MAX = 50, 300   # expected range for FAQ/glossary entries
OVERLAP_SENTENCES = 2     # sentences carried from prev sub-chunk into next
OVERLAP_MAX_TOKENS = 120  # ceiling on that overlap

ATOMIC_DOCS = {"faq", "glossary"}   # everything else is a "guide"

DOCS_DIR = Path("documents")
OUT_PATH = Path("chunks.jsonl")

_TOK = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")


def n_tokens(text: str) -> int:
    return len(_TOK.encode(text, add_special_tokens=False))


def parse_header(md: str):
    """Pull the `# Title` + `Source: <url>` preamble off a cleaned doc."""
    title = re.search(r"^# (.+)$", md, re.M)
    src = re.search(r"^Source:\s*(\S+)$", md, re.M)
    title = title.group(1).strip() if title else ""
    src = src.group(1).strip() if src else ""
    # body = everything after the Source line
    body = md
    if src:
        body = md.split(src, 1)[1]
    # Drop any in-body H1 (Starlight repeats the page title as a `#` heading in
    # the content); it's redundant with the title we prepend and would otherwise
    # become a heading-only stub chunk.
    body = re.sub(r"^# .+$", "", body, flags=re.M)
    return title, src, body.strip()


def split_into_blocks(text: str):
    """Split text into blank-line-separated blocks, keeping fenced code blocks
    whole (a ``` ... ``` span is returned as a single block)."""
    lines = text.split("\n")
    blocks, cur, in_fence = [], [], False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
            cur.append(ln)
            continue
        if ln.strip() == "" and not in_fence:
            if cur:
                blocks.append("\n".join(cur).strip())
                cur = []
        else:
            cur.append(ln)
    if cur:
        blocks.append("\n".join(cur).strip())
    return [b for b in blocks if b]


def split_sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def tail_overlap(text: str) -> str:
    """Last 1-2 sentences of `text`, capped at OVERLAP_MAX_TOKENS, to seed the
    next sub-chunk. Skips code so we never duplicate a half command."""
    if "```" in text:
        return ""
    sents = split_sentences(text)[-OVERLAP_SENTENCES:]
    ov = " ".join(sents)
    while sents and n_tokens(ov) > OVERLAP_MAX_TOKENS:
        sents = sents[1:]
        ov = " ".join(sents)
    return ov


def split_section_by_size(header: str, content: str):
    """Sub-split an oversized guide section on block boundaries, prepending the
    header to each piece (breadcrumb) and a sentence overlap from the previous
    piece. Code blocks stay intact."""
    blocks = split_into_blocks(content)
    sub_texts, cur = [], []

    def flush():
        if cur:
            sub_texts.append("\n\n".join(cur))

    for b in blocks:
        trial = "\n\n".join(cur + [b])
        if cur and n_tokens(trial) > MAX_TOKENS:
            flush()
            cur = [b]
        else:
            cur.append(b)
    flush()

    out = []
    for i, body in enumerate(sub_texts):
        if i == 0:
            out.append(body)            # first piece already starts with the header
            continue
        # later pieces lost the header when split off — re-add it as a breadcrumb,
        # plus a 1-2 sentence overlap carried from the previous piece.
        parts = [header] if header else []
        ov = tail_overlap(sub_texts[i - 1])
        if ov:
            parts.append(ov)
        parts.append(body)
        out.append("\n\n".join(parts))
    return out


def split_guide(md: str):
    """Header-based split, parent-bounded merge of small siblings, then size-cap
    recursion on anything still over the cap. Returns [(section, text)].

    Why the merge pass: splitting on every header alone produces many tiny
    "stub" sections (a heading + one transitional sentence) that aren't
    retrievable on their own. We greedily merge consecutive sections that share
    the same level-2 (`##`) parent, up to MIN_TOKENS, so stubs fold into their
    siblings while distinct top-level topics stay separate (limits the
    representation-dilution risk from Anticipated Challenge #2)."""
    title, src, body = parse_header(md)

    # Pass 1: raw sections, tagging each with its current `##` parent. Track
    # fence state so a `##` inside a code block isn't mistaken for a header.
    lines = body.split("\n")
    raw, head, level, parent, cur, in_fence = [], title or "Introduction", 1, title, [], False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
        m = re.match(r"^(#{2,6})\s+(.+)$", ln) if not in_fence else None
        if m:
            if cur:
                raw.append((head, level, parent, "\n".join(cur).strip()))
            level = len(m.group(1))
            head = m.group(2).strip()
            if level <= 2:
                parent = head           # new top-level topic
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        raw.append((head, level, parent, "\n".join(cur).strip()))
    raw = [r for r in raw if r[3].strip()]

    # Pass 2: merge within parent (<= MIN_TOKENS), then size-split over MAX.
    chunks = []
    acc_heads, acc_text, acc_parent = [], [], None

    def flush():
        nonlocal acc_heads, acc_text, acc_parent
        if not acc_text:
            return
        text = "\n\n".join(acc_text)
        label = acc_heads[0] if len(acc_heads) == 1 else f"{acc_parent} ({len(acc_heads)} sections)"
        chunks.append((label, text))
        acc_heads, acc_text, acc_parent = [], [], None

    for head, lvl, par, content in raw:
        if n_tokens(content) > MAX_TOKENS:           # long section -> stands alone, size-split
            flush()
            header_line = content.split("\n", 1)[0] if content.lstrip().startswith("#") else f"## {head}"
            for sub in split_section_by_size(header_line, content):
                chunks.append((head, sub))
            continue
        merged = "\n\n".join(acc_text + [content])
        if acc_text and (par != acc_parent or n_tokens(merged) > MIN_TOKENS):
            flush()
        acc_parent = par
        acc_heads.append(head)
        acc_text.append(content)
    flush()
    return title, src, chunks


def split_faq(md: str):
    """One chunk per Q&A (split on `---`). No overlap between entries."""
    title, src, body = parse_header(md)
    entries = [e.strip() for e in re.split(r"^---$", body, flags=re.M) if e.strip()]
    out = []
    for e in entries:
        q = re.search(r"\*\*(.+?)\*\*", e)
        section = q.group(1).strip() if q else "FAQ entry"
        out.append((section, e))
    return title, src, out


def split_glossary(md: str):
    """One chunk per `- **Term**` bullet. No overlap between entries."""
    title, src, body = parse_header(md)
    out = []
    lead = []
    for ln in body.split("\n"):
        if ln.startswith("- "):
            term = re.search(r"\*\*(.+?)\*\*", ln)
            section = term.group(1).strip() if term else "Glossary entry"
            out.append((section, ln[2:].strip()))
        elif not ln.startswith("#") and ln.strip():
            lead.append(ln.strip())
    if lead:
        out.insert(0, ("Nautilus Glossary (intro)", " ".join(lead)))
    return title, src, out


def main():
    records = []
    cid = 0
    print(f"Chunking {DOCS_DIR}/  (cap {MAX_TOKENS} tok, atomic {ATOMIC_MIN}-{ATOMIC_MAX})\n")
    for path in sorted(glob.glob(str(DOCS_DIR / "*.md"))):
        slug = Path(path).stem
        md = Path(path).read_text(encoding="utf-8")
        if slug == "faq":
            dtype, (title, src, secs) = "faq", split_faq(md)
        elif slug == "glossary":
            dtype, (title, src, secs) = "glossary", split_glossary(md)
        else:
            dtype = "guide"
            title, src, secs = split_guide(md)

        for section, text in secs:
            cid += 1
            records.append({
                "id": cid,
                "doc": slug,
                "type": dtype,
                "section": section,
                "source_url": src,
                "token_count": n_tokens(text),
                "text": text,
            })
        print(f"  {slug:<26} {len(secs):>3} chunks")

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(records)} chunks -> {OUT_PATH}")


if __name__ == "__main__":
    main()
