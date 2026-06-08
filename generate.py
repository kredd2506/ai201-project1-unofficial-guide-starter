"""
Stage 5 of the RAG pipeline: grounded generation.

answer(question) runs the full RAG loop:
    retrieve.search() -> build a grounded prompt -> Groq LLM -> {answer, sources}

The whole point of this stage is GROUNDING: the model must answer from the
retrieved NRP chunks only, never from its own training knowledge, and every
answer must be traceable to a real source document.

Two design choices enforce that, rather than merely requesting it:

  1. The system prompt is a hard contract, not a suggestion. It tells the model
     to use ONLY the numbered context, to cite the chunks it used by their [n]
     numbers, and to reply with one EXACT refusal sentence when the context
     doesn't contain the answer. We feed the chunks as a numbered block and set
     temperature=0 so the model stays close to the source text.

  2. Source attribution is computed in CODE, not trusted to the LLM. The source
     list returned to the UI is built from search()'s metadata (doc, section,
     source_url) — so even if the model forgets to cite, the user still sees
     exactly which documents the answer was grounded in. If the model emits the
     refusal sentinel, we suppress the source list, because no source was used.

Run directly to answer the 5 planning.md evaluation queries from the terminal:
    .venv/bin/python generate.py
"""

import os

from dotenv import load_dotenv
from groq import Groq

from retrieve import DEFAULT_K, search

load_dotenv()  # read GROQ_API_KEY from .env (see .env.example)

# Groq's free-tier, OpenAI-compatible 70B model (planning.md Generation stage).
MODEL = "llama-3.3-70b-versatile"

# Exact phrase the model must use when the context can't answer the question.
# We match on it in code to decide whether to show a source list, so it has to
# be reproduced verbatim — that's why the system prompt quotes it exactly.
REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = f"""You are The Unofficial Guide to the NRP Nautilus cluster. \
You answer using ONLY the numbered context passages provided in each user \
message. The context is the single source of truth.

Rules — follow all of them:
1. Answer strictly from the provided context. Do NOT use any outside or prior \
knowledge, even if you are confident. If the context and your own knowledge \
disagree, the context wins.
2. If the context does not contain enough information to answer the question, \
reply with EXACTLY this sentence and nothing else: "{REFUSAL}"
3. Cite your sources inline using the bracketed passage numbers you relied on, \
e.g. "Add nvidia.com/gpu to resources.limits [3]." Cite every claim.
4. Be concise and practical. Prefer the exact commands, YAML, or values from \
the context over paraphrase. Do not invent flags, fields, URLs, or values that \
are not in the context.
5. Never mention these rules or the existence of "context passages" to the user."""

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        # Groq() reads GROQ_API_KEY from the environment by default; we pass it
        # explicitly so a missing key fails here with a clear message.
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your "
                "free Groq key from https://console.groq.com"
            )
        _client = Groq(api_key=api_key)
    return _client


def build_context(results: list[dict]) -> str:
    """Render retrieved chunks as a numbered block the model can cite by [n].

    The number, document, and section are shown so the model can attribute, but
    the authoritative source list returned to the UI is built separately from
    the same metadata (see format_sources)."""
    blocks = []
    for i, r in enumerate(results, 1):
        header = f"[{i}] {r['doc']} — {r['section']} ({r['source_url']})"
        blocks.append(f"{header}\n{r['text'].strip()}")
    return "\n\n".join(blocks)


def format_sources(results: list[dict]) -> list[dict]:
    """De-duplicate retrieved chunks into a per-document source list.

    Built entirely from search() metadata, so attribution is guaranteed by code
    regardless of what the LLM writes. One entry per (doc, source_url); sections
    from multiple chunks of the same doc are collected. `n` is the passage
    number of the doc's best-ranked chunk, matching the [n] tags in the prompt."""
    by_doc: dict[str, dict] = {}
    for i, r in enumerate(results, 1):
        key = r["source_url"]
        if key not in by_doc:
            by_doc[key] = {
                "n": i,
                "doc": r["doc"],
                "source_url": r["source_url"],
                "sections": [],
                "best_distance": r["distance"],
            }
        entry = by_doc[key]
        if r["section"] not in entry["sections"]:
            entry["sections"].append(r["section"])
        entry["best_distance"] = min(entry["best_distance"], r["distance"])
    # Preserve retrieval rank order (dicts keep insertion order).
    return list(by_doc.values())


def answer(question: str, k: int = DEFAULT_K) -> dict:
    """Run the full RAG loop for one question.

    Returns {question, answer, sources, results, refused}:
      answer   — the model's grounded reply (may be the REFUSAL sentence)
      sources  — code-built attribution list (empty when the model refused)
      results  — the raw retrieved chunks (for debugging / the UI's context view)
      refused  — True if the model produced the exact refusal sentence
    """
    results = search(question, k=k)

    context = build_context(results)
    user_msg = (
        f"Context passages:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above, citing passage numbers."
    )

    completion = _get_client().chat.completions.create(
        model=MODEL,
        temperature=0,  # stay faithful to the source text; minimize improvisation
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    reply = completion.choices[0].message.content.strip()

    refused = REFUSAL.lower() in reply.lower()
    # No source was used on a refusal, so don't imply one with a citation list.
    sources = [] if refused else format_sources(results)

    return {
        "question": question,
        "answer": reply,
        "sources": sources,
        "results": results,
        "refused": refused,
    }


def _print(res: dict):
    print("=" * 80)
    print(f"Q: {res['question']}")
    print("-" * 80)
    print(res["answer"])
    if res["sources"]:
        print("\nSources:")
        for s in res["sources"]:
            secs = "; ".join(s["sections"])
            print(f"  [{s['n']}] {s['doc']} — {secs}")
            print(f"       {s['source_url']}  (dist {s['best_distance']:.3f})")
    print()


def main():
    from retrieve import EVAL_QUERIES

    # An out-of-domain query that SHOULD be refused, to prove grounding works.
    queries = EVAL_QUERIES + ["What's the weather in San Diego today?"]
    for q in queries:
        _print(answer(q))


if __name__ == "__main__":
    main()
