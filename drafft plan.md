# planning.md — GT CS Unofficial Guide (RAG System)

## Project Overview

**System name:** GT CS Unofficial Guide
**Domain:** CS professor and course reviews at Georgia Tech
**Goal:** A retrieval-augmented system that lets students ask natural language questions about courses, professors, workload, and degree requirements — and get answers grounded in real student experiences.

---

## Why This Knowledge Is Hard to Find Otherwise

Student knowledge about GT CS courses is scattered across Reddit threads, Rate My Professors, and informal Discord channels. There's no single place to ask "which section of Algorithms has the fairest grader" or "is CS 3600 a good pair with OS?" A student has to manually browse multiple platforms, filter noise, and synthesize advice — this system does that for them.

---

## Milestone 1 — Domain & Documents ✅

### Domain Summary
CS course and professor reviews at Georgia Tech. Sources include Rate My Professors, r/gatech Reddit threads, the official GT course catalog, and student-aggregated GitHub repos.

### Source Documents
See [`sources.md`](./sources.md) for full list with URLs, skim notes, and coverage check.

**Source count:** 10 identified (target: 10 minimum)
**Question coverage:** 5 specific questions documented in sources.md

### Key Observations from Skimming
- RMP reviews: short, dense, self-contained → simple chunking
- Reddit threads: long, noisy → need smarter chunking strategy
- Catalog entries: highly structured → chunk by course
- GitHub data: variable → evaluate per repo

---

## Milestone 2 — Chunking Strategy (Planned)

| Source Type | Chunk Strategy | Target Chunk Size |
|-------------|---------------|-------------------|
| RMP reviews | One chunk per review | ~100–200 tokens |
| Reddit comments | One chunk per top-level comment | ~150–300 tokens |
| Catalog entries | One chunk per course (title + prereqs + description) | ~100–150 tokens |
| GitHub/CSV | One row or structured entry per chunk | TBD |

**Open questions to resolve in M2:**
- How to handle Reddit threads with 100+ comments — filter by upvotes?
- Should prof name be included in every chunk as metadata, or embedded in text?
- Overlap between chunks: needed for Reddit long-form posts?

---

## Milestone 3 — Embedding & Retrieval (Planned)

- Embedding model: TBD (likely `text-embedding-3-small` or similar)
- Vector store: TBD (Chroma, FAISS, or Pinecone)
- Retrieval strategy: top-k cosine similarity; consider MMR for diversity

---

## Milestone 4 — Generation (Planned)

- LLM: TBD
- Prompt design: include retrieved chunks + source metadata in context
- Output format: direct answer + cited sources

---

## Milestone 5 — Evaluation (Planned)

**Evaluation questions (draft):**
1. Which professor teaches CS 3510 most clearly?
2. Is CS 3600 heavy to pair with OS?
3. What do students say about [Professor X]'s grading?
4. What are the prereqs for CS 4641?
5. Which Intro CS section fills up fastest?

**Metrics to track:**
- Retrieval precision (are the right chunks coming back?)
- Answer faithfulness (does the answer match the retrieved docs?)
- Answer relevance (does it actually answer the question?)

---

## Open Decisions / Risks

| Decision | Options | Status |
|----------|---------|--------|
| Vector store | Chroma vs FAISS vs Pinecone | Undecided |
| Embedding model | OpenAI vs open-source | Undecided |
| Reddit scraping | PRAW API vs manual copy | Undecided |
| RMP scraping | Manual vs scraper | Need to check ToS |

---

## Commit Log

| Milestone | Commit message | Status |
|-----------|---------------|--------|
| M1 | `feat: add sources.md and planning.md` | ⬜ TODO |
| M2 | `feat: chunking pipeline` | ⬜ TODO |
| M3 | `feat: embedding and vector store` | ⬜ TODO |
| M4 | `feat: retrieval + generation pipeline` | ⬜ TODO |
| M5 | `feat: evaluation harness` | ⬜ TODO |
