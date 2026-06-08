"""
Stage 3 of the RAG pipeline: embedding + vector store.

Reads chunks.jsonl (from chunk.py), embeds every chunk with
nomic-ai/nomic-embed-text-v1.5, and loads the vectors into a persistent
ChromaDB collection along with per-chunk metadata for later attribution.

Why nomic-embed-text-v1.5 (see planning.md Retrieval Approach):
  Its 8192-token window comfortably fits our 800-token guide cap, so NO chunk
  is truncated at embedding time. 46% of our chunks exceed 256 tokens, so the
  common all-MiniLM-L6-v2 (256-token window) would silently truncate nearly
  half the corpus. nomic uses the same BERT WordPiece tokenizer family our
  token counts were computed with, so chunk sizes are unaffected by the choice.

nomic prompt prefixes (REQUIRED — the model was trained with them):
  - documents are embedded as "search_document: <text>"
  - queries  are embedded as "search_query: <text>"   (see retrieve.py)
  Mixing these up, or omitting them, measurably degrades retrieval. We embed
  with the document prefix here.

Vector store: ChromaDB, cosine distance. We compute embeddings ourselves with
sentence-transformers and hand the raw vectors to Chroma (collection has no
embedding_function), so the SAME nomic model + prefixes are used at index time
and query time. With normalized vectors, Chroma's cosine "distance" is
1 - cosine_similarity, so 0.0 = identical and lower = more relevant.

Run:  .venv/bin/python embed.py
"""

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("chunks.jsonl")
DB_DIR = Path("chroma_db")          # persisted vector store (git-ignored)
COLLECTION = "nrp_docs"
MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
DOC_PREFIX = "search_document: "    # nomic's required document prefix


def load_chunks(path: Path):
    """Read chunks.jsonl into a list of dicts (one per line)."""
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_model() -> SentenceTransformer:
    # trust_remote_code: nomic ships custom modeling code with the weights;
    # sentence-transformers needs permission to import it.
    return SentenceTransformer(MODEL_NAME, trust_remote_code=True)


def build_collection(model: SentenceTransformer, chunks: list):
    """Embed every chunk and (re)build the Chroma collection from scratch."""
    client = chromadb.PersistentClient(path=str(DB_DIR))

    # Rebuild cleanly so re-running never leaves stale vectors behind.
    if COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION)
    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},   # cosine distance, matches normalized vectors
    )

    texts = [DOC_PREFIX + c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks with {MODEL_NAME} ...")
    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,           # unit vectors -> cosine distance well-behaved
        show_progress_bar=True,
    )

    collection.add(
        ids=[str(c["id"]) for c in chunks],
        embeddings=embeddings.tolist(),
        documents=[c["text"] for c in chunks],   # store RAW text (no prefix) for display
        metadatas=[
            {
                "doc": c["doc"],                 # source document slug (for attribution)
                "section": c["section"],         # heading / FAQ-Q / glossary term
                "source_url": c["source_url"],   # canonical NRP.ai URL
                "type": c["type"],               # guide | faq | glossary
                "position": i,                   # chunk's order in the corpus
                "token_count": c["token_count"],
            }
            for i, c in enumerate(chunks)
        ],
    )
    return collection


def main():
    chunks = load_chunks(CHUNKS_PATH)
    model = load_model()
    collection = build_collection(model, chunks)
    print(f"\nDone: {collection.count()} vectors in collection '{COLLECTION}' -> {DB_DIR}/")
    print("Embedding dim:", model.get_sentence_embedding_dimension())


if __name__ == "__main__":
    main()
