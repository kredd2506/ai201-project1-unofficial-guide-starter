"""
Stage 4 of the RAG pipeline: retrieval.

search(query, k=5) embeds the query with the SAME nomic model used in embed.py
(with the "search_query: " prefix this time) and returns the top-k most
relevant chunks from the ChromaDB collection, each with its source metadata and
cosine distance.

Run directly to smoke-test retrieval against the planning.md evaluation queries:
    .venv/bin/python retrieve.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

from embed import COLLECTION, DB_DIR, MODEL_NAME

QUERY_PREFIX = "search_query: "     # nomic's required query prefix (see embed.py)
DEFAULT_K = 5                       # planning.md Retrieval Approach: top-k = 5

# Module-level singletons so the model + DB are loaded once, not per query.
_model = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(DB_DIR))
        _collection = client.get_collection(COLLECTION)
    return _collection


def search(query: str, k: int = DEFAULT_K) -> list[dict]:
    """Return the top-k chunks for `query`, ranked by ascending cosine distance.

    Each result: {text, distance, doc, section, source_url, type, position}.
    `distance` is cosine distance in [0, 2]: 0 = identical, lower = more relevant.
    """
    model = _get_model()
    collection = _get_collection()

    q_emb = model.encode(
        [QUERY_PREFIX + query],
        normalize_embeddings=True,
    )
    res = collection.query(
        query_embeddings=q_emb.tolist(),
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma nests results one level deep (one list per query); we sent one query.
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    return [
        {"text": doc, "distance": dist, **meta}
        for doc, meta, dist in zip(docs, metas, dists)
    ]


def _print_results(query: str, results: list[dict]):
    print("=" * 80)
    print(f"QUERY: {query}")
    print("-" * 80)
    for rank, r in enumerate(results, 1):
        snippet = " ".join(r["text"].split())[:280]
        print(f"[{rank}] dist={r['distance']:.3f}  {r['doc']}  —  {r['section']}")
        print(f"     {r['source_url']}")
        print(f"     {snippet}{'...' if len(r['text']) > 280 else ''}")
        print()


# The 5 planning.md Evaluation Plan questions.
EVAL_QUERIES = [
    "As a student, how do I get access to the NRP Nautilus cluster?",
    "Why did the data in my pod disappear after it restarted, and how do I prevent it?",
    "How do I request a GPU for my pod?",
    "What happens if I run a job with a sleep command that never ends?",
    "What types of data am I not allowed to store on NRP?",
]


def main():
    for q in EVAL_QUERIES:
        _print_results(q, search(q))


if __name__ == "__main__":
    main()
