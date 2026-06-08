# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
The dommain is running research workloads on the NRP nautilus cluster ( from access, GPU/batch jobs, storage , LLMs, policies, troubleshooting, etc).
It is valuable because NRP is a valuable NSF funded compute for students, profeesors and academia, but the initial onboarding can be a hard, especially for those not from a computer science domain. 
the official channels, have a lot of doc pages, with a weak search and a single question often spans across multiple pages. And also the docs assume, that the users are fluent with Kubernetes and are aware of NRP's policies.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Getting Started | How to get access: CILogon login, namespace membership, kubectl/kubelogin setup | https://nrp.ai/documentation/userdocs/start/getting-started |
| 2 | Using Nautilus | Best practices for using the cluster; namespaces and core workflow | https://nrp.ai/documentation/userdocs/start/using-nautilus |
| 3 | Cluster Policies | Rules users must follow (no sleep jobs, no force-delete, fair use) | https://nrp.ai/documentation/userdocs/start/policies |
| 4 | FAQ | Atomic question-and-answer entries about common cluster issues | https://nrp.ai/documentation/userdocs/start/faq |
| 5 | Glossary | Definitions of NRP/Kubernetes terms (pod, namespace, etc.) in NRP's own terms | https://nrp.ai/documentation/userdocs/start/glossary |
| 6 | Asking for Support | How and where to get help (Matrix, support channels) | https://nrp.ai/documentation/userdocs/start/support |
| 7 | GPU Pods | How to request and run a pod with a GPU | https://nrp.ai/documentation/userdocs/running/gpu-pods |
| 8 | Running Batch Jobs | Submitting batch jobs that run and exit on their own | https://nrp.ai/documentation/userdocs/running/jobs |
| 9 | Storage Intro | Overview of storage options and the stateless-container problem | https://nrp.ai/documentation/userdocs/storage/intro |
| 10 | Persistent Storage (Ceph) | Using Ceph FS/RBD persistent volumes so data survives pod restarts | https://nrp.ai/documentation/userdocs/storage/ceph |
| 11 | Moving Data | Getting data in and out of the cluster | https://nrp.ai/documentation/userdocs/storage/move-data |
| 12 | NRP Managed LLM | Overview of NRP-hosted LLMs: available models, chat interfaces, API access | https://nrp.ai/documentation/userdocs/ai/llm-managed |
| 13 | Tutorial: Introduction | Entry-point tutorial orienting new users to the platform | https://nrp.ai/documentation/userdocs/tutorial/introduction |
| 14 | Tutorial: Basic Kubernetes | Hands-on basics: creating pods, core kubectl commands | https://nrp.ai/documentation/userdocs/tutorial/basic |
| 15 | Tutorial: Docker and Containers | Container fundamentals and building images for the cluster | https://nrp.ai/documentation/userdocs/tutorial/docker |
| 16 | Tutorial: Debugging | Fixing pods that won't start and other troubleshooting | https://nrp.ai/documentation/userdocs/tutorial/debugging |
| 17 | ML/Jupyter Pod | Running a Jupyter notebook pod for interactive ML work | https://nrp.ai/documentation/userdocs/jupyter/jupyter-pod |
| 18 | Disclaimers | Protected-data policy (no HIPAA/PID/FISMA/FERPA storage) — extracted section only; added in Milestone 4 to cover eval Q5 | https://nrp.ai/documentation/#disclaimers |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->
   I will split the documents with a recursive size cap chunking strategy.
   the primary split is structural. Header based for guides, entry based for FAQ/ glossary. so one chunk , will be one idea.
  

**Chunk size:** 500-800 tokens per chunk. 
Atomic entries will be between 50-300 tokens.

**Overlap:** 1-2 sentences (80-120 tokens)

**Reasoning:** The corpus is structurally heterogeneous; the header/entry boundaries already mark the semantic units, so splitting on them preserves the answer bearing context, while a size cap + light overlap protects the few long setions.

**Implementation note (Milestone 3):** Pure header-splitting produced many tiny "stub" sections (a heading + one transitional sentence) that aren't retrievable alone. Added a **parent-bounded merge** pass: consecutive sections sharing the same `##` parent are merged up to ~500 tokens, so stubs fold into their siblings while distinct top-level topics stay separate (limits the dilution risk from Challenge #2). Final corpus: **118 chunks** (median 209 tok, max 798, none truncated). Atomic FAQ/glossary entries kept one-per-chunk with no inter-entry overlap, as specified.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** nomic-ai/nomic-embed-text-v1.5 via sentence-transformers (768-dim, 8192-token window).
*Changed during Milestone 3 (chunking).* Originally bge-small-en-v1.5, but its window is only **512 tokens** — it would silently truncate our 500–800-token guide chunks at embedding time (the exact coupling flagged in the chunking notes: max chunk ≤ model window). nomic-embed's **8192-token window** comfortably fits the full 800-token cap, so no chunk is truncated. bge-base/large are also 512, so they wouldn't solve it. Token counts are identical (both BERT WordPiece), so the chunk sizes are unaffected by the swap.

**Top-k:** 5

**Production tradeoff reflection:**
Accuracy on domain-specific text — NRP/Kubernetes jargon ("namespace", "pod", "Ceph RBD", kubelogin). A larger model (bge-large, or an API model like OpenAI text-embedding-3-large / Voyage voyage-3) embeds technical terms more faithfully → fewer near-miss retrievals. Best case: a domain-fine-tuned embedder.
Context length — your longest guide sections + code blocks benefit from a bigger window (nomic's 8K) so nothing truncates. Trade: higher dim = more storage + slower search.
Latency vs. accuracy — API models are more accurate but add network round-trips and per-query cost; local models are free and private but cap out lower. For an interactive guide, sub-second retrieval matters.
Multilingual — likely not needed here (docs are English-only); honest to say you'd deprioritize it for this corpus, which shows you're reasoning about your domain rather than listing features.
Storage/scale — 768-dim vs 384-dim doubles your vector store size; trivial at 17 docs, real at millions.


---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | As a student, how do I get access to the NRP Nautilus cluster? | Log in to the NRP portal via CILogon using your institution, then ask your research supervisor to add you to their namespace; once added, your status changes to a cluster `user` with access to that namespace's resources. (Source: Getting Started) |
| 2 | Why did the data in my pod disappear after it restarted, and how do I prevent it? | Containers are stateless — all data is gone forever when the container restarts unless it is stored on a persistent volume. To keep data, store it on persistent storage such as a Ceph PVC. (Source: Getting Started / Storage) |
| 3 | How do I request a GPU for my pod? | Add `nvidia.com/gpu` to the container's `resources.limits` (and `requests`) in the pod/job YAML, e.g. `nvidia.com/gpu: 1`. Limits: up to 2 GPUs per pod, up to 8 per node for jobs; specific high-memory GPUs use a typed resource like `nvidia.com/a100`. (Source: GPU Pods) |
| 4 | What happens if I run a job with a `sleep` command (or any command that never ends)? | You will be banned from using the cluster. Jobs must run a real workload and exit on their own; a `Job` with a `sleep` command or equivalent (any command that never ends by itself) is prohibited. (Source: Cluster Policies / Getting Started) |
| 5 | What types of data am I not allowed to store on NRP? | NRP has no storage suitable for protected data — HIPAA, PID, FISMA, or FERPA-protected data of any kind may not be stored on NRP machines. (Source: Disclaimers, https://nrp.ai/documentation/#disclaimers) |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Code blocks and commands split or mangled across chunk boundaries.**
   Our guides are full of multi-line shell commands and YAML (the kubelogin install
   block, the kubectl config steps, GPU pod specs). Naive fixed-length splitting is
   known to orphan code from the sentence that explains when to run it, leaving
   fragments the retriever misinterprets. If a chunk returns the *command* without the
   surrounding "run this after X" context — or worse, returns half a YAML block — the
   user gets an answer that's incomplete or actively wrong. Our mitigation is keeping
   fenced code blocks intact during chunking and splitting on headings/paragraphs
   rather than raw character counts, but it's the most likely place to see bad
   retrievals, and we'll watch for it in evaluation.

2. **Off-topic retrieval from jargon that's reused across many pages.**
   Terms like "namespace", "pod", "storage", and "GPU" appear on nearly every page,
   so a query like "how do I request a GPU?" can pull a chunk that merely *mentions*
   GPUs in passing (e.g. a monitoring or policy page) instead of the actual gpu-pods
   instructions. This is the classic representation-dilution problem: when a chunk
   covers several themes, the specific fact gets averaged out of its embedding. Our
   type-aware chunking (one section = one idea) reduces this, but overlapping
   vocabulary across the corpus makes near-miss retrieval a real risk we'll need to
   check with our test questions.

3. **Stale instructions and version drift.**
   The docs reference specific tools, ports, commands, and URLs that change over time,
   and NRP periodically reorganizes pages and moves content between them. Because we
   snapshot the docs at index time, our system can confidently return a procedure that
   NRP has since changed, with no signal to the user that it's outdated. Unlike risks 1
   and 2, this is an ingestion/lifecycle issue rather than a chunking one: we'll record
   the snapshot date and treat the index as needing periodic refresh rather than
   one-and-done.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │                          INDEXING (run once)                          │
  └──────────────────────────────────────────────────────────────────────┘

   [1] Ingestion          [2] Chunking            [3] Embed + Store
  ┌───────────────┐     ┌────────────────┐     ┌──────────────────────┐
  │ 17 NRP.ai doc │     │ structure-aware│     │ nomic-embed-text     │
  │ pages saved   │ ──▶ │ split + size   │ ──▶ │ v1.5 (sentence-tr.)  │
  │ to documents/ │     │ cap (headers / │     │        │             │
  │ (.md / .txt)  │     │ per-entry)     │     │        ▼             │
  └───────────────┘     └────────────────┘     │ vector store: Chroma │
                                                └──────────┬───────────┘
                                                           │
  ┌────────────────────────────────────────────────────────┼─────────────┐
  │                       QUERY (per question)              │             │
  └────────────────────────────────────────────────────────┼─────────────┘
                                                            ▼
   user question        [4] Retrieval            [5] Generation
  ┌───────────────┐     ┌────────────────┐     ┌──────────────────────┐
  │ "How do I     │     │ embed query →  │     │ LLM (Claude) answers │
  │  request a    │ ──▶ │ cosine top-k=5 │ ──▶ │ from retrieved chunks│
  │  GPU?"        │     │ from store     │     │ + cites source docs  │
  └───────────────┘     └────────────────┘     └──────────┬───────────┘
                                                           ▼
                                                  grounded, cited answer
```

**Stage → tool/library**

| Stage | Tool / library |
|-------|----------------|
| 1. Ingestion | NRP.ai doc pages saved as local `.md`/`.txt` in `documents/` |
| 2. Chunking | Python — structure-aware splitter (header / per-entry) with recursive size cap |
| 3. Embedding + Vector Store | `nomic-ai/nomic-embed-text-v1.5` (8192-token window) via `sentence-transformers` → ChromaDB (cosine) |
| 4. Retrieval | Embed query, cosine similarity, top-k = 5 |
| 5. Generation | LLM (Claude) conditioned on retrieved chunks, with source attribution |

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
- **Tool:** Claude (Claude Code).
- **Input:** the Documents table (17 NRP.ai URLs) plus the Chunking Strategy section. I'll ask it to write `ingest.py` (fetch each page, strip nav/HTML, save clean `.md`/`.txt` into `documents/`) and `chunking.py` implementing the structure-aware splitter — header-based for guides, per-entry for FAQ/glossary, with the 500–800-token cap (50–300 for atomic entries), ~1–2 sentence overlap on sub-splits only, and code fences kept intact.
- **Expected output:** two scripts and a `chunks.jsonl` where each record has `{text, source_url, section}`.
- **Verify:** spot-check that no chunk splits a fenced code block, that FAQ/glossary chunks are one entry each, and that chunk token counts fall in the stated ranges; eyeball 5–10 chunks against the live pages.

**Milestone 4 — Embedding and retrieval:**
- **Tool:** Claude.
- **Input:** the Retrieval Approach section. I'll ask it to write `embed.py` (encode every chunk with `nomic-ai/nomic-embed-text-v1.5` via sentence-transformers, store vectors + metadata in a persistent ChromaDB collection) and `retrieve.py` (`search(query, k=5)` returning the top-k chunks with their source URLs and cosine distances).
- **Expected output:** a built ChromaDB collection plus a `search()` function that returns ranked chunks with attribution.
- **Verify:** run each of the 5 Evaluation Plan questions through `search()` and confirm the correct source doc appears in the top-5 (e.g. the GPU question returns the gpu-pods chunk); check that nomic's `search_query:`/`search_document:` prefixes and L2-normalization are applied so cosine distances are sensible.

**Milestone 4 — retrieval results (run on the 5 eval queries, top-k=5):**
- **Q1 access** ✅ rank 1 = `getting-started / Get access and log in` (dist 0.16).
- **Q2 data lost on restart** ✅ (with a caveat) the answer is retrieved at **rank 5** — last slot in top-5 — behind three vocabulary-overlap distractors ("pod stuck Terminating", `kubectl delete/create`, batch-job logs) that share words like *pod/restart/delete* without answering the question. **Known limitation, deliberately left as-is.** Root cause: the answer ("Containers are stateless… data gone forever… unless a persistent volume") sits inside a *merged 3-topic* `getting-started` chunk (namespace-token-refresh + the stateless warning + external links), which dilutes its embedding (Challenge #2). Investigated fixes before deciding: isolating the warning callout as its own chunk would lift Q2 to **rank 2** (measured: dist 0.316→0.275), but we chose not to re-chunk since k=5 already captures the answer and the generator will see it. Notable finding from the investigation: the *clean, focused* glossary "Stateless" entry ranks only **37th** for this query — its abstract definition never says "data lost / restart / persistent volume", showing that content/intent alignment, not chunk cleanliness alone, drives retrieval.
- **Q3 GPU** ✅ ranks 2–5 all `gpu-pods`, incl. the YAML with `nvidia.com/gpu` (dist 0.20).
- **Q4 sleep job** ✅ right sources in top-5 (`jobs`, `policies`).
- **Q5 prohibited data (HIPAA/FERPA/FISMA)** — *first run:* ❌ **corpus-coverage gap, not a retrieval bug.** A `grep` confirmed no ingested chunk mentioned HIPAA/FERPA/FISMA: the answer lived only in the **Disclaimers** section of the docs landing page (`/documentation/#disclaimers`), which was not one of the 17 ingested user-doc pages. *Fix:* extended `ingest.py` to extract **only** that disclaimer section into `disclaimers.md` (source #18) — ingesting the whole landing page would have buried the policy among navigation link-cards and diluted its embedding (Challenge #2). *After re-embedding (119 chunks):* ✅ rank 1 = `disclaimers / Disclaimers` (dist **0.171**), with a wide margin to rank 2 (0.332). **All 5 eval queries now retrieve their answer in the top-5.** This is the milestone's intended lesson: testing retrieval before generation surfaced a corpus gap that would otherwise have looked like an LLM hallucination at Milestone 5.

**Milestone 5 — Generation and interface:**
- **Tool:** Claude (both to write the code and as the answer-generating LLM at runtime).
- **Input:** the Architecture diagram and the retrieval output format. I'll ask it to write the RAG loop — take a question, call `search()`, build a grounded prompt ("answer only from these chunks; cite the source URL; say so if the answer isn't present"), call the LLM, and a small CLI/Streamlit interface.
- **Expected output:** an end-to-end app that answers a typed question with a cited, source-grounded response.
- **Verify:** run all 5 Evaluation Plan questions end-to-end and compare against the expected answers I already verified against the docs; confirm answers cite the right source and that an out-of-domain question ("what's the weather?") is correctly refused rather than hallucinated.
