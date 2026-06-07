# Project Journal — The Unofficial Guide (Project 1)

> Running log of decisions, learnings, and pivots. Newest entries on top.

---

## 2026-06-07 — Milestone 2 COMPLETED: planning.md fully drafted

- **Documents table populated** in `planning.md` — settled on **17 NRP.ai user-doc pages** (added Tutorial: Introduction, Docker/Containers, and ML/Jupyter Pod to the original 14). Admin guide deliberately excluded — wrong audience.
- **Chunking strategy = structure-aware with a recursive size cap.** Primary split is structural: header-based for the long guides, per-entry for FAQ/glossary, so one chunk = one idea.
  - Chunk size: **500–800 tokens** for guide sections; atomic entries **50–300 tokens**.
  - Overlap: **1–2 sentences (~80–120 tokens)**, applied only on sub-splits — not between independent FAQ/glossary entries (overlapping unrelated entries just adds noise).
  - Rationale: the corpus is structurally heterogeneous, so a single fixed chunk size would hurt. Splitting on existing semantic boundaries preserves answer-bearing context; the size cap + light overlap protect the few long sections.
- **Embedding model = `BAAI/bge-small-en-v1.5`** via sentence-transformers (384 dim, 512-token window).
  - Picked over the default all-MiniLM-L6-v2 because MiniLM's **256-token cap would truncate the 500–800-token guide chunks** — the exact failure the chunking design avoids. bge-small keeps similar speed/dims but fits the chunks. Fallback: MiniLM *only* if chunk cap drops to 256.
  - Coupling to remember: max chunk size must stay ≤ the model's token window, or we embed truncated text.
- **Top-k = 5.** Several test questions (access flow, stateless-data fix) need facts spanning 2+ docs, so k=3 risks dropping a source; k=5 is the RAG sweet spot. May tune down to 3 for atomic queries after eval.
- **Production reflection** written: domain-jargon accuracy and context length are the levers worth paying for; multilingual deprioritized (English-only corpus); noted the 768-vs-384 dim storage tradeoff.
- **Evaluation Plan = 5 questions with doc-verified expected answers.** Fetched the live NRP pages (getting-started, policies, gpu-pods, AUP) and confirmed each expected answer verbatim; fixed Q5's attribution (the HIPAA/FERPA/FISMA/PID disclaimer lives in the site disclaimer/AUP, not the policies body) and sharpened Q3 with the real `nvidia.com/gpu` syntax + limits (≤2/pod, ≤8/node for jobs).
- **Anticipated Challenges = 3:** (1) code/YAML split across chunk boundaries, (2) off-topic retrieval from jargon reused across pages (representation dilution), (3) stale instructions / version drift — deliberately spanning retrieval-quality, retrieval-precision, and data-freshness.
- **Architecture:** ASCII diagram split into Indexing (ingest → chunk → embed/FAISS) and Query (question → retrieve top-5 → generate) phases, plus a stage→tool table. Open picks: vector store = FAISS (vs Chroma), generation LLM = Claude (could swap to an NRP-managed LLM for thematic tie-in).
- **AI Tool Plan:** per-milestone (M3 ingest/chunk, M4 embed/retrieve, M5 generate/interface), each naming tool · input planning section · expected output · verification — verification loops back to the 5 eval questions as the acceptance test.
- **Status:** every planning.md section now filled (Domain → AI Tool Plan). Milestone 2 deliverable complete.
- **Commits:** `a64bfe5` (docs table), `138a697` (chunking + retrieval), then this commit (eval/challenges/architecture/AI-tool-plan). Pushed to origin/main.
- **Next (Milestone 3):** implement `ingest.py` + `chunk.py` per the AI Tool Plan; populate `documents/`.

---

Domain vs. source (the distinction the milestone cares about)
Your domain is how to actually run research workloads on the NRP Nautilus cluster — getting access, running GPU/batch jobs, storage, hosted LLMs, policies, and troubleshooting. Your source is the NRP documentation site, and each doc page is one source document. That's a legitimate setup: the milestone explicitly counts "pages" as documents.
One scoping note: the docs contain a big Admin guide (cluster upgrades, Ceph recovery, FIONA installs, etc.) aimed at people running the platform, not using it. I'd exclude the admin guide and scope to the user journey. That narrowing is what keeps your 10+ sources answering a range of user questions instead of drifting into an unrelated audience.
Your 10+ source documents
These are deliberately spread across access, policy, compute, storage, AI, and troubleshooting so they don't all say the same thing:

Getting Started (access/login/kubectl) — https://nrp.ai/documentation/userdocs/start/getting-started
Using Nautilus — https://nrp.ai/documentation/userdocs/start/using-nautilus
Cluster Policies — https://nrp.ai/documentation/userdocs/start/policies
FAQ — https://nrp.ai/documentation/userdocs/start/faq
Glossary — https://nrp.ai/documentation/userdocs/start/glossary
Asking for Support — https://nrp.ai/documentation/userdocs/start/support
GPU pods — https://nrp.ai/documentation/userdocs/running/gpu-pods
Running batch jobs — https://nrp.ai/documentation/userdocs/running/jobs
Storage intro — https://nrp.ai/documentation/userdocs/storage/intro
Persistent storage (Ceph FS/RBD) — https://nrp.ai/documentation/userdocs/storage/ceph
Moving data in/out — https://nrp.ai/documentation/userdocs/storage/move-data
NRP Managed LLM overview — https://nrp.ai/documentation/userdocs/ai/llm-managed
Tutorial: Basic Kubernetes — https://nrp.ai/documentation/userdocs/tutorial/basic
Tutorial: Debugging — https://nrp.ai/documentation/userdocs/tutorial/debugging

That's 14, giving you headroom to drop a couple that turn out thin. One caution on the https://nrp.ai/live/ page you linked: it looks like a live/dynamic page, which makes a poor static RAG source (content changes, no stable facts to retrieve). Prefer the doc pages above. If you want genuine source-type variety, the AUP PDF (https://nrp.ai/NRP-AUP.pdf) is a different format you could add.
What I noticed skimming (this drives Milestone 2)
The pages are heterogeneous, and that's the single most important thing for your chunking design:

Long guides (Getting Started) are multi-section, with headings, fenced code blocks, and callout admonitions ("Required", "Read it before using"). Key facts are spread across paragraphs and concentrated in callouts — e.g., "containers are stateless, your data is gone on restart" sits in a callout, while the kubelogin port-fix is buried in a code snippet.
FAQ and Glossary are atomic — one Q&A or one term per unit, short and self-contained.

So a single fixed chunk size will hurt you: the FAQ/glossary want per-entry chunks, while the long guides want header-delimited section chunks (and you'll want to keep code blocks intact rather than splitting mid-snippet). Flagging this now will make Milestone 2 much easier.
5+ questions your system should answer
Specific enough that you can verify the answer lives in your docs:

How does a student get access to NRP Nautilus? (getting-started: log in via CILogon, then have your supervisor add you to their namespace)
Why did my pod's data disappear after it restarted, and how do I prevent it? (getting-started + storage: containers are stateless; use a persistent volume)
How do I request a GPU in my pod? (gpu-pods)
What happens if I run a job with a sleep command? (policies/getting-started: you get banned)
How do I fix the kubelogin "port 8000 already in use" error? (getting-started: --listen-address)
What kinds of data am I not allowed to store on NRP? (disclaimer: no HIPAA/FERPA/FISMA/PID data)
Which LLMs does NRP host and how do I access them? (llm-managed)

---

## 2026-06-07 — Pivot: dropping Georgia Tech, switching domain to NRP.ai

- **Decision:** stop all work on the Georgia Tech CS course/professor-review domain and start over with a new, unrelated domain centered on **NRP.ai**.
- **Repo cleanup:** restored `planning.md` and `README.md` to the original starter templates and removed the GA Tech artifacts (`sources.md`, `drafft plan.md`). Kept this journal and the preflight commit. History was left intact (forward cleanup commit, no rewrite).
- **Next:** define the NRP.ai domain, its document sources, and 5 test questions from scratch.

---

## 2026-06-07 — Georgia Tech attempt (superseded) — learnings worth keeping

> The GA Tech domain was abandoned, but these are generalizable to the NRP.ai work.

- **Verify every URL before committing it.** On the GA Tech list, an RMP "department" URL silently filtered nothing (reused the *school* id as a *department* id and returned unrelated results), and several pages 404'd / blocked. Always fetch-check first.
- **This is RAG over a *local* corpus.** The pipeline reads files from `documents/`; it does not fetch live URLs at query time. A URL failing in a fetcher is only a *verification* nuisance — what matters is whether each source's text can get into `documents/` once. A source is only disqualified if it can't be ingested *at all*.
- **Aim for format diversity, not 10 near-identical pages.** A good corpus spans short opinion reviews (→ per-review chunks), structured data/JSON (→ parse, don't text-chunk), prose docs (→ per-section/entry chunks), and numeric tables (→ structured records). This directly drives the chunking strategy.
- **JS single-page apps need their API, not the rendered page.** Some review sites load content client-side, so a fetcher sees an empty page — ingest from the underlying API/data export instead of scraping HTML.
- **"Official" pages can hide their structured fields.** Catalog-style sites often keep key data (e.g., prerequisites, requirement lists) in sidebars or rendered tabs that a naive HTML-to-text scrape drops → those need targeted extraction.
- **Reddit blocks automated access.** Every Reddit endpoint (`www`, `old`, `.json`) returns an anti-bot **"network security / blocked"** page (HTTP 403) to unauthenticated requests, regardless of user-agent — confirmed from this environment. To use Reddit you need the official API (OAuth/PRAW) or to manually save threads into `documents/`. Treat Reddit as a low-priority, high-effort supplement, not a primary source.
