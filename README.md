# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This system answers practical questions about **running research workloads on the NRP (National Research Platform) Nautilus cluster** — the full user journey: getting access, running GPU and batch jobs, persistent storage, NRP-hosted LLMs, cluster policies, and troubleshooting.

This knowledge is valuable because NRP is a large, NSF-funded Kubernetes compute resource that's free to students, faculty, and academic researchers — but onboarding is genuinely hard, especially for people outside computer science. It's hard to get from the official channels for three concrete reasons: (1) the documentation is spread across many pages with weak built-in search, so a single real question ("why did my data vanish and how do I stop it?") spans several pages; (2) the docs assume fluency with Kubernetes concepts (pods, namespaces, PVCs) that newcomers don't have; and (3) some load-bearing facts live outside the user docs entirely — e.g. the protected-data policy (no HIPAA/PID/FISMA/FERPA) sits in a disclaimer on the landing page, not in the policies guide. A grounded RAG assistant that retrieves across all of these at once and cites its sources closes that gap.

---

## Document Sources

All sources are pages from the official NRP documentation site (`nrp.ai`). Each page is ingested as one source document by `ingest.py` (raw HTML saved to `documents/raw/`, cleaned Markdown to `documents/`). They are deliberately spread across access, policy, compute, storage, AI, and troubleshooting so the corpus answers a *range* of user questions rather than repeating one topic. The administrator guide (cluster upgrades, Ceph recovery, FIONA installs) was deliberately excluded — it targets people *running* the platform, not *using* it.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Getting Started (access, CILogon login, kubectl/kubelogin) | Guide | https://nrp.ai/documentation/userdocs/start/getting-started |
| 2 | Using Nautilus (best practices, core workflow) | Guide | https://nrp.ai/documentation/userdocs/start/using-nautilus |
| 3 | Cluster Policies (no sleep jobs, no force-delete, fair use) | Policy | https://nrp.ai/documentation/userdocs/start/policies |
| 4 | FAQ (atomic Q&A on common cluster issues) | FAQ | https://nrp.ai/documentation/userdocs/start/faq |
| 5 | Glossary (NRP/Kubernetes terms) | Glossary | https://nrp.ai/documentation/userdocs/start/glossary |
| 6 | Asking for Support (Matrix, support channels) | Guide | https://nrp.ai/documentation/userdocs/start/support |
| 7 | GPU Pods (requesting/running a GPU pod) | Guide | https://nrp.ai/documentation/userdocs/running/gpu-pods |
| 8 | Running Batch Jobs | Guide | https://nrp.ai/documentation/userdocs/running/jobs |
| 9 | Storage Intro (stateless-container problem) | Guide | https://nrp.ai/documentation/userdocs/storage/intro |
| 10 | Persistent Storage — Ceph FS/RBD | Guide | https://nrp.ai/documentation/userdocs/storage/ceph |
| 11 | Moving Data in/out | Guide | https://nrp.ai/documentation/userdocs/storage/move-data |
| 12 | NRP Managed LLM (hosted models, chat/API access) | Guide | https://nrp.ai/documentation/userdocs/ai/llm-managed |
| 13 | Tutorial: Introduction | Tutorial | https://nrp.ai/documentation/userdocs/tutorial/introduction |
| 14 | Tutorial: Basic Kubernetes (pods, kubectl) | Tutorial | https://nrp.ai/documentation/userdocs/tutorial/basic |
| 15 | Tutorial: Docker and Containers | Tutorial | https://nrp.ai/documentation/userdocs/tutorial/docker |
| 16 | Tutorial: Debugging (pods that won't start) | Tutorial | https://nrp.ai/documentation/userdocs/tutorial/debugging |
| 17 | ML/Jupyter Pod | Guide | https://nrp.ai/documentation/userdocs/jupyter/jupyter-pod |
| 18 | Disclaimers (no HIPAA/PID/FISMA/FERPA data) — *extracted section only* | Policy/Disclaimer | https://nrp.ai/documentation/#disclaimers |

**Note on source #18:** the protected-data disclaimer lives only on the docs *landing* page, not on any of the 17 user-doc pages. Evaluation question 5 can't be answered without it, so `ingest.py` extracts **just that section** (rather than the whole landing page, which is otherwise navigation link-cards that would dilute the disclaimer's embedding). This gap was discovered by testing retrieval before generation — see the Failure Case / Spec Reflection notes.

---

## Chunking Strategy

The corpus is **structurally heterogeneous** — long multi-section guides with code/YAML alongside atomic FAQ Q&As and one-line glossary terms — so a single fixed chunk size would hurt. The chunker (`chunking.py`) is **structure-aware with a recursive size cap**: the primary split follows the document's own structure so that *one chunk = one idea*.

**Preprocessing (before chunking).** `ingest.py` fetches each page, strips site nav/header/footer/right-sidebar TOC/buttons/icon SVGs, and converts the body (`div.sl-markdown-content`) to clean Markdown. Two careful steps preserve answer-bearing content: Starlight callouts/asides (e.g. "containers are stateless") are converted to labeled `**Note — …:**` headings instead of being dropped, and multi-line code blocks are reassembled from the renderer's per-line `<div>`s and emitted as fenced ```` ``` ```` blocks (so YAML/shell isn't collapsed onto one line). The chunker then splits on this Markdown structure.

**Chunk size:** Guide sections target **500–800 tokens** (hard cap 800); atomic FAQ/glossary entries are **50–300 tokens**, one entry per chunk. Token counts use the BERT WordPiece tokenizer — identical to what the embedding model (nomic) sees — so the cap is a faithful bound on what gets embedded.

**Overlap:** **1–2 sentences (~80–120 tokens)**, applied **only** when an oversized guide section is sub-split on paragraph boundaries. **No overlap** is added between independent FAQ/glossary entries — overlapping unrelated entries just injects noise.

**Splitting rules.** Guides split on Markdown headers (any level); FAQ splits per `---` (one Q&A); glossary splits per `- **Term**` bullet. A guide section over the 800-token cap is sub-split on paragraph boundaries, and a fenced code block is treated as **one unsplittable paragraph** so commands/YAML are never cut mid-block (mitigates Anticipated Challenge #1).

**Parent-bounded merge (refinement during implementation).** Pure header-splitting produced many tiny "stub" sections (a heading + one transitional sentence) that aren't retrievable on their own. A merge pass folds consecutive sections sharing the same `##` parent up to ~500 tokens, so stubs join their siblings while distinct top-level topics stay separate. (This merge is also the root cause of the Q2 retrieval failure — see Failure Case Analysis — a real trade-off between avoiding stubs and avoiding multi-theme dilution.)

**Why these choices fit the documents:** the header/entry boundaries already mark the semantic units, so splitting on them keeps each answer's context intact; the size cap + light overlap protect the few long sections; and keeping code fences whole is essential because the guides are full of multi-line `kubectl`/YAML that's useless if fragmented.

**Final chunk count:** **119 chunks** (median 209 tokens, max 798, none truncated) across the 18 sources.

### Sample Chunks

Five representative chunks pulled from `chunks.jsonl`, spanning all three chunk types (guide / glossary / FAQ) and the full size range (50–781 tokens). Each was inspected against a two-part standalone test — **(a) is it self-contained** (could someone answer a question from this chunk alone, with no neighbors?) and **(b) is it about a single idea** (so its embedding isn't diluted across themes)? — because every chunk is retrieved in isolation and handed to the LLM with no surrounding context.

**Sample 1 — source: `disclaimers` · section "Disclaimers" · type guide · 50 tokens** *(answers eval Q5)*
```
## Disclaimers

The National Research Platform currently has no storage that is suitable for HIPAA,
PID, FISMA, FERPA, or protected data of any kind. Users are not permitted to store
such data on NRP machines.
```
*Inspection: self-contained ✅, single-idea ✅. The whole protected-data policy in one focused chunk — this is why Q5 retrieves at rank 1 with a wide margin.*

**Sample 2 — source: `gpu-pods` · section "Running GPU pods" · type guide · 288 tokens** *(answers eval Q3)*
````
## Running GPU pods

Use this definition to create your own pod and deploy it to kubernetes:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod-example
spec:
  containers:
  - name: gpu-container
    image: tensorflow/tensorflow:latest-gpu
    command: ["sleep", "infinity"]
    resources:
      limits:
        nvidia.com/gpu: 1
      requests:
        nvidia.com/gpu: 1
```

This example requests 1 GPU device. You can have up to 8 per node if you're using
jobs, and up to 2 for pods. If you request GPU devices in your pod, kubernetes will
auto schedule your pod to the appropriate node.
````
*Inspection: self-contained ✅, single-idea ✅. The fenced YAML is kept intact (the explicit goal of Anticipated Challenge #1) — the request mechanism (`nvidia.com/gpu` under `resources.limits`/`requests`) and the runnable spec live together in one chunk.*

**Sample 3 — source: `glossary` · section "Namespace" · type glossary · 85 tokens**
```
**Namespace** In Kubernetes, a namespace is a virtual cluster within the physical
cluster. It provides a way to partition and organize resources within a Kubernetes
cluster, allowing multiple users, teams, or projects to share the same cluster
without interfering with each other. Namespaces help in creating isolated
environments and preventing naming conflicts between different resources.
```
*Inspection: self-contained ✅, single-idea ✅. An atomic glossary entry — exactly one definition per chunk, with no inter-entry overlap.*

**Sample 4 — source: `faq` · section "My pod is stuck Terminating." · type faq · 190 tokens**
```
**My pod is stuck Terminating.**

> This happens for a few reasons, such as:
> - The node running your pod went offline. The pod will finish terminating once
>   the node is back online.
> - The storage attached to the pod can't be unmounted.
> - Due to high load on the node, your pod termination process could not complete.
>   In all these cases, ask a cluster admin in Matrix chat, or wait for somebody to fix it.
> Note — Do Not Force delete your pod:
> Do not use `kubectl delete --grace-period=0 --force` to delete stuck pods!
> It will keep resources attached to the node for an indefinite period and will
> require rebooting the node.
```
*Inspection: self-contained ✅, single-idea ✅. One FAQ question = one chunk. (This is one of the vocabulary-overlap distractors that out-ranks the real Q2 answer — it shares "pod/restart/delete" without answering "why did my data disappear?" — see Failure Case Analysis.)*

**Sample 5 — source: `getting-started` · section "Get access and log in" · type guide · 781 tokens (near the 800-token cap)** *(answers eval Q1; abridged below)*
```
### Get access and log in

If you are a new user and want to access the NRP Nautilus cluster, follow the steps below.
1. Point your browser to the NRP Nautilus portal (https://nrp.ai).
2. Click the Log In button at the top right corner.
3. You will be redirected to the CILogon page, where you Select an Identity Provider.
4. Select your institution from the menu and click Log On.
   - ... (Microsoft / Google / GitHub fallbacks if your institution isn't listed) ...
6. If you are a student, contact your research supervisor and ask them to add you to
   their namespace. Once added, your status changes to a cluster user and you get
   access to all namespace resources.
7. If you are faculty/researcher/postdoc, request to be promoted to a namespace admin
   in Matrix ...
```
*Inspection: self-contained ✅, single-idea ✅ (the complete "get access and log in" procedure). This is the largest chunk in the corpus — it sits just under the 800-token cap, showing the size cap holding a long multi-step guide section together as one unit instead of fragmenting the login flow.*

---

## Embedding Model

**Model used:** `nomic-ai/nomic-embed-text-v1.5` via `sentence-transformers` (768-dim, **8192-token context window**), stored in a persistent ChromaDB collection with cosine distance. Vectors are L2-normalized and computed by us (Chroma holds no embedding function), so the *same* model is used at index and query time. nomic requires task prefixes, which we apply: documents are embedded as `search_document: …` and queries as `search_query: …` — omitting or swapping them measurably degrades retrieval.

*Why nomic (a deliberate change during implementation):* the original plan was `BAAI/bge-small-en-v1.5`, but its window is only **512 tokens** — it would silently truncate our 500–800-token guide chunks at embedding time, the exact coupling our chunking design is built to avoid (max chunk size must be ≤ the model's window). bge-base/large are also 512, so they wouldn't fix it. nomic's 8192-token window comfortably fits the 800-token cap so **no chunk is truncated**, and because both use the same BERT WordPiece tokenizer, our token counts and chunk sizes are unaffected by the swap.

**Production tradeoff reflection:** If this were deployed for real users and cost weren't a constraint, the levers I'd weigh:
- **Accuracy on domain-specific text** — this corpus is dense with NRP/Kubernetes jargon ("namespace", "pod", "Ceph RBD", "kubelogin"). A larger model (bge-large) or an API model (OpenAI `text-embedding-3-large`, Voyage `voyage-3`) embeds technical terms more faithfully → fewer near-miss retrievals; the ideal would be a domain-fine-tuned embedder. This is the lever I'd pay for first, because our one weak result (Q2) is a precision problem.
- **Context length** — already solved by nomic's 8K window; nothing truncates. Trade-off: bigger models / higher dims cost more storage and slower search.
- **Latency vs. accuracy** — API models are more accurate but add a network round-trip and per-query cost; local models are free and private but cap out lower. For an interactive guide, sub-second retrieval matters, so I'd benchmark before moving off local.
- **Multilingual** — the docs are English-only, so I'd honestly *deprioritize* multilingual capacity for this corpus rather than list it as a feature.
- **Storage/scale** — 768-dim vs 384-dim doubles the vector store; trivial at 119 chunks, but real at millions.

---

## Retrieval Test Examples

The top-k chunks returned for three eval queries, captured directly from `search()` (`.venv/bin/python retrieve.py`). Each row is one retrieved chunk; **distance is cosine distance in [0, 2] — lower = more relevant.** A fourth example (Q2, the weak case) and its full top-5 are dissected in the [Failure Case Analysis](#failure-case-analysis) below.

### Example A — "As a student, how do I get access to the NRP Nautilus cluster?"

| Rank | Distance | Returned chunk (doc — section) |
|------|----------|--------------------------------|
| **1** | **0.160** | **`getting-started` — Get access and log in** |
| 2 | 0.179 | `using-nautilus` — Using Nautilus |
| 3 | 0.193 | `using-nautilus` — How to use the cluster |
| 4 | 0.222 | `tutorial-introduction` — Getting Help |
| 5 | 0.228 | `faq` — How do I acknowledge support from NRP in research papers? |

**Why these chunks are relevant:** Rank 1 is the literal step-by-step access procedure (CILogon login → supervisor adds you to a namespace → you become a cluster `user`) — a direct, complete answer, and at **0.160 the lowest distance of any eval query**, so it clearly dominates. Ranks 2–3 are the adjacent onboarding context — what Nautilus *is* and the three ways to use it — relevant supporting material a new user would also want. The rank-5 acknowledgment FAQ is a weak vocabulary-overlap pull (shares "NRP", "research") that doesn't answer the question, but it's harmless: it sits far behind rank 1 and the grounded answer cites only `[1]`.

### Example B — "How do I request a GPU for my pod?"

| Rank | Distance | Returned chunk (doc — section) |
|------|----------|--------------------------------|
| 1 | 0.197 | `policies` — Requesting GPUs |
| 2 | 0.210 | `gpu-pods` — Requesting special GPUs |
| **3** | **0.228** | **`gpu-pods` — Running GPU pods *(the pod YAML with `nvidia.com/gpu`)*** |
| 4 | 0.235 | `gpu-pods` — GPU Pods |
| 5 | 0.303 | `gpu-pods` — Choosing GPU type |

**Why these chunks are relevant:** Four of the five chunks are from `gpu-pods` — the correct document — including **rank 3, which carries the exact pod spec** (`nvidia.com/gpu: 1` under `resources.limits`/`requests`) that *is* the answer. An honest wrinkle: **rank 1 is a `policies` near-miss**, not `gpu-pods`. The `policies` "Requesting GPUs" chunk edges out the how-to YAML by 0.031 because the query phrase "request a GPU" lexically matches the policy heading "Requesting GPUs" — but that chunk is about GPU *etiquette* (don't reserve GPUs you won't use), not the request mechanism. This is exactly the vocabulary-overlap risk from Anticipated Challenge #2; it's benign here only because `top-k = 5` still delivers the YAML chunk to the generator, which grounds the answer correctly.

### Example C — "What types of data am I not allowed to store on NRP?"

| Rank | Distance | Returned chunk (doc — section) |
|------|----------|--------------------------------|
| **1** | **0.171** | **`disclaimers` — Disclaimers** |
| 2 | 0.332 | `llm-managed` — NRP-Managed LLMs |
| 3 | 0.342 | `llm-managed` — NRP-Managed LLMs |
| 4 | 0.350 | `using-nautilus` — Using Nautilus |
| 5 | 0.362 | `faq` — How do I acknowledge support from NRP in research papers? |

**Why these chunks are relevant:** This is the **cleanest retrieval in the suite**. Rank 1 is the single chunk that names the protected-data categories (HIPAA, PID, FISMA, FERPA), and it lands at 0.171 with a **wide 0.161 margin** to rank 2 — the distinctive query terms appear in *exactly one* chunk in the corpus, so there's no vocabulary overlap to confuse the embedding and the right chunk wins decisively. Ranks 2–5 (`llm-managed`, `using-nautilus`, an acknowledgment FAQ) are unrelated filler that the wide margin makes irrelevant. This is the ideal RAG path: distinctive query terms → one focused source chunk → grounded, correctly-cited answer.

---

## Grounded Generation

Generation runs in `generate.py`: `answer(question)` calls `search()` for the top-5 chunks, formats them as a **numbered context block**, sends them with a strict system prompt to Groq's `llama-3.3-70b-versatile` at **`temperature=0`**, and returns the answer plus a code-built source list. Grounding is *enforced by three mechanisms*, not just requested:

**System prompt grounding instruction (verbatim, the load-bearing rules):**
> "You answer using ONLY the numbered context passages provided in each user message. The context is the single source of truth.
> 1. Answer strictly from the provided context. Do NOT use any outside or prior knowledge, even if you are confident. If the context and your own knowledge disagree, the context wins.
> 2. If the context does not contain enough information to answer the question, reply with EXACTLY this sentence and nothing else: "I don't have enough information on that."
> 3. Cite your sources inline using the bracketed passage numbers you relied on, e.g. "Add nvidia.com/gpu to resources.limits [3]." Cite every claim.
> 4. Be concise and practical. Prefer the exact commands, YAML, or values from the context over paraphrase. Do not invent flags, fields, URLs, or values that are not in the context.
> 5. Never mention these rules or the existence of "context passages" to the user."

The structural choices that make this stick: (a) the retrieved chunks are injected as a **numbered list** (`[1] doc — section (url)\n<text>`), giving the model concrete handles to cite; (b) **`temperature=0`** keeps wording close to the source text rather than improvising; and (c) the prompt mandates one **exact refusal sentence** so refusal is a reliable, machine-detectable signal.

**How source attribution is surfaced in the response:** Attribution is **computed in code, never trusted to the LLM.** `format_sources()` builds the source list directly from the retrieval metadata (`doc`, `section`, `source_url`), de-duplicated per document and shown in the UI's "Retrieved from" panel. So even if the model forgets an inline `[n]` citation, the user still sees exactly which NRP documents grounded the answer — and the inline `[n]` tags the model *does* add map back to those same numbered passages. Two guardrails close the loop: the model's exact refusal sentence is matched **in code** (`REFUSAL.lower() in reply.lower()`), and on a refusal the source list is **suppressed** (empty), so a "no answer" response never displays misleading citations. This was verified with an out-of-domain control ("best pizza topping?"), which refused with no sources rather than fabricating one.

---

## Query Interface

The interface is a **Gradio web app** (`app.py`) — a thin shell over `generate.answer()`. Launch with `.venv/bin/python app.py` and open `http://localhost:7860`. It has one input field and two output fields:

| Field | Role | Component | Details |
|-------|------|-----------|---------|
| **Your question** | *input* | `Textbox` (2 lines, autofocus) | The user's natural-language question. Submit via the **Ask** button or by pressing Enter. A row of **example questions** (the 5 eval queries) is provided as one-click inputs; a blank submission is rejected with "Please enter a question." |
| **Answer** | *output* | `Textbox` (8 lines) | The grounded reply from the LLM, with inline `[n]` citations pointing at the numbered passages it used. On an out-of-domain question this is the exact refusal sentence. |
| **Retrieved from** | *output* | `Textbox` (4 lines) | The **code-built** source list (`[n] doc — section(s)` + URL), assembled from retrieval metadata, not from the model. On a refusal it instead reads `(no sources — the docs don't cover this question)`, so a "no answer" response never shows misleading citations. |

**Sample interaction transcript (a complete query and response, from an actual run):**

```
┌─ Your question ─────────────────────────────────────────────────────────────┐
│ As a student, how do I get access to the NRP Nautilus cluster?               │
└─────────────────────────────────────────────────────────────────────────────┘
                                  [ Ask ]

┌─ Answer ────────────────────────────────────────────────────────────────────┐
│ Log in to the NRP Nautilus portal and select your institution on the        │
│ CILogon page, then ask your research supervisor to add you to their          │
│ namespace; once added, your status changes to a cluster user with access     │
│ to all namespace resources [1].                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Retrieved from ────────────────────────────────────────────────────────────┐
│ [1] getting-started — Get access and log in                                  │
│     https://nrp.ai/documentation/userdocs/start/getting-started             │
└─────────────────────────────────────────────────────────────────────────────┘
```

The inline `[1]` in the answer maps to passage `[1]` in the "Retrieved from" box — the same numbering the model was given in its context — so every claim is traceable to a real NRP document.

**Refusal transcript (out-of-domain question — the other output state):**

```
┌─ Your question ─────────────────────────────────────────────────────────────┐
│ What is the best pizza topping?                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                  [ Ask ]

┌─ Answer ────────────────────────────────────────────────────────────────────┐
│ I don't have enough information on that.                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Retrieved from ────────────────────────────────────────────────────────────┐
│ (no sources — the docs don't cover this question)                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Evaluation Report

_Run end-to-end through `generate.answer()` (retrieval → grounded Groq `llama-3.3-70b-versatile`). Distances are cosine; lower = more relevant. Sources are the code-built attribution list shown in the UI._

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | As a student, how do I get access to the NRP Nautilus cluster? | Log in to the NRP portal via CILogon (select your institution), then ask your research supervisor to add you to their namespace; your status then changes to a cluster `user` with access to that namespace's resources. | "Log in to the NRP Nautilus portal and select your institution on the CILogon page, then ask your research supervisor to add you to their namespace; once added, your status changes to a cluster user with access to all namespace resources [1]." Cited `getting-started` (rank 1, dist 0.160). | Relevant — `getting-started / Get access and log in` is rank 1. | **Accurate** — names CILogon login, the supervisor/namespace step, and the status change. |
| 2 | Why did the data in my pod disappear after it restarted, and how do I prevent it? | Containers are stateless — all data is gone forever when the container restarts unless stored on a persistent volume (e.g. a Ceph PVC). | "Containers are stateless; 'all your data will be gone forever when the container restarts, unless you store it in a persistent volume' — so store your data on a persistent volume [5]." Cited `getting-started` (rank 5, dist 0.316). | Partially relevant — the answer-bearing `getting-started` chunk lands at **rank 5** behind vocabulary-overlap distractors (`pod stuck Terminating`, deployment/job chunks); still inside top-5, so the generator saw it. | **Accurate** — correctly identifies statelessness and the persistent-volume fix (doesn't name "Ceph" specifically, but the prevention is right). |
| 3 | How do I request a GPU for my pod? | Add `nvidia.com/gpu` to the container's `resources.limits` (and `requests`), e.g. `nvidia.com/gpu: 1`; up to 2 GPUs/pod, 8/node for jobs; typed resources like `nvidia.com/a100` for specific GPUs. | Returned the exact pod YAML with `nvidia.com/gpu: 1` under `resources.limits`/`requests` [3], and noted `nvidia.com/a100` for special GPU types [2]. Cited `gpu-pods` (rank 2, dist 0.210). | Relevant — `gpu-pods` chunks fill ranks 2–5, including the YAML; rank 1 is a `policies` near-miss. | **Accurate** — correct request mechanism + typed-resource detail. Omits the numeric caps (2/pod, 8/node), which were supplementary to the question. |
| 4 | What happens if I run a job with a `sleep` command (or any command that never ends)? | You will be banned from the cluster; jobs must run a real workload and exit on their own — a `Job` with `sleep` (or any non-terminating command) is prohibited. | "If you run a job with a sleep command that never ends, you will be banned from using the cluster [1][2][3][5]." Cited `jobs` (rank 1, dist 0.284) and `policies`. | Relevant — `jobs` rank 1, `policies` and `getting-started` also in top-5. | **Accurate** — states the ban correctly (concise; doesn't add the "must exit on its own" rationale). |
| 5 | What types of data am I not allowed to store on NRP? | NRP has no storage suitable for protected data — HIPAA, PID, FISMA, or FERPA-protected data of any kind may not be stored on NRP machines. | "You are not permitted to store HIPAA, PID, FISMA, FERPA, or protected data of any kind on NRP machines [1]." Cited `disclaimers` (rank 1, dist 0.171). | Relevant — `disclaimers` rank 1 with a wide margin to rank 2 (0.171 vs 0.332). | **Accurate** — exact protected-data list with correct source. |

**Out-of-domain control (grounding check):** "What is the best pizza topping?" → the system returned the exact refusal sentence (`"I don't have enough information on that."`) and showed **no sources**, instead of hallucinating an answer.

**Summary:** 5/5 accurate; retrieval relevant on 4/5, partially relevant on Q2 (correct chunk present but at rank 5 — see Failure Case Analysis).

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** Q2 — "Why did the data in my pod disappear after it restarted, and how do I prevent it?" This is a *retrieval-quality* failure, not a generation one: the final answer was correct, but the retriever very nearly missed the chunk that makes it correct.

**What the system returned:** The answer was right ("containers are stateless; data is gone on restart unless stored on a persistent volume"). But the answer-bearing chunk — `getting-started / Getting Started with NRP Nautilus` — came back at **rank 5 of 5** (cosine distance 0.316), the last slot in top-k. Ranks 1–4 were vocabulary-overlap distractors that share words like *pod / restart / delete* without answering the question: `faq / My pod is stuck Terminating` (0.248), two `tutorial-basic` deployment chunks (0.280), and a `jobs` batch chunk (0.304). With our `top-k = 5`, the right chunk was the last one to make the cut; at `k = 4` the system would have had nothing to ground on and would have refused or guessed.

**Root cause (tied to a specific pipeline stage):** The **chunking** stage, propagating into **embedding**. The actual fact ("All your data will be gone forever when the container restarts, unless you store it in a persistent volume") lives inside a *merged, multi-topic* `getting-started` chunk — the parent-bounded merge pass in `chunking.py` folded the stateless-container warning together with two unrelated topics (namespace token-refresh and a block of external links) to clear the tiny-stub threshold. When the embedding model averages a chunk covering three themes into one vector, the specific "data lost on restart" signal gets diluted by the surrounding token-refresh/link text, so the chunk's embedding sits *farther* from the query than chunks that merely repeat the query's surface vocabulary. This is exactly Anticipated Challenge #2 (representation dilution from multi-theme chunks) observed in practice. We confirmed it's dilution, not missing content, by measurement: isolating the stateless warning into its own chunk moves Q2 from rank 5 to **rank 2** (distance 0.316 → 0.275). A second finding from the same investigation: the *clean, focused* glossary "Stateless" entry ranks only **37th** for this query — its abstract definition never uses the words "data lost / restart / persistent volume," showing the problem is content/intent alignment, not chunk cleanliness alone.

**What you would change to fix it:** Split the stateless-container warning callout into its own chunk instead of merging it into the larger `getting-started` section, so its embedding represents that single idea (measured to lift Q2 to rank 2). More generally, exempt semantically distinct callouts/admonitions from the parent-bounded merge so a high-value warning is never averaged in with adjacent unrelated prose. Lower-effort alternatives we considered: keep `k = 5` (the answer is already captured, so the generator succeeds — which is why we deliberately left it as-is for this milestone), or add a light reranker over the top-k to reorder by query relevance rather than raw embedding distance.

---

## Spec Reflection

**One way the spec helped guide my implementation:** The spec's Evaluation Plan — 5 questions with doc-verified expected answers — and the AI Tool Plan that made those questions the *acceptance test for retrieval* shaped the order I built things in. Following it, I ran all 5 questions through `search()` *before* wiring up the LLM, and Q5 ("what data can't I store?") returned nothing relevant; a `grep` confirmed no ingested chunk mentioned HIPAA/FERPA/FISMA, because that disclaimer lived only on the docs landing page, outside my 17 user-doc sources. Because the spec forced me to test retrieval first, this read as a **corpus-coverage gap** I could fix at ingestion (extracting just the disclaimer section as source #18, which lifted Q5 to rank 1) rather than as a mysterious LLM hallucination discovered much later. The spec essentially told me *where* to look when something was wrong.

**One way my implementation diverged from the spec, and why:** My spec's first draft named `bge-small-en-v1.5` as the embedding model, but I diverged and switched to `nomic-embed-text-v1.5` during implementation. The reason was a constraint the spec itself stated but I hadn't reconciled: chunk size must be ≤ the embedding model's context window, and bge-small's window is only 512 tokens — it would have *silently truncated* my 500–800-token guide chunks at embedding time, quietly corrupting retrieval. nomic's 8192-token window fits the 800-token cap with room to spare, and because both models share the same BERT WordPiece tokenizer, none of my chunk sizes changed. After making the swap I updated `planning.md`'s Retrieval Approach section so the spec stayed truthful rather than letting code and spec drift apart.

---

## AI Usage

I used **Claude (via Claude Code)** as my AI tool throughout. For each stage I gave it the relevant section of `planning.md` as the spec, then reviewed and overrode its output rather than accepting it wholesale. Three specific instances:

**Instance 1 — Ingestion + chunking (Milestone 3)**

- *What I asked the AI to do:* using the Documents table (the 17 NRP.ai URLs) and my Chunking Strategy section, write `ingest.py` (fetch each page, strip nav/HTML, save clean Markdown to `documents/`) and `chunking.py` (the structure-aware splitter: header-based for guides, per-entry for FAQ/glossary, 500–800-token cap, light overlap on sub-splits only, code fences kept intact).
- *What it produced:* working scripts that split on Markdown structure and wrote `chunks.jsonl`, but the first chunker did pure header-splitting and the first ingester collapsed multi-line code blocks onto one line.
- *What I changed, overrode, or directed differently:* I directed two fixes it didn't do on its own. First, pure header-splitting produced many tiny "stub" chunks (a heading + one sentence) that aren't retrievable, so I had it add a **parent-bounded merge** pass (fold consecutive same-parent sections up to ~500 tokens). Second, I found the Starlight "Expressive Code" renderer puts each source line in its own `<div>` with no newline, so YAML/`kubectl` blocks were being flattened; I directed it to rejoin those per-line divs so fenced code stays multi-line (critical for Anticipated Challenge #1).

**Instance 2 — Embedding + retrieval (Milestone 4)**

- *What I asked the AI to do:* from my Retrieval Approach section, write `embed.py` (encode every chunk, store vectors + metadata in a persistent ChromaDB collection) and `retrieve.py` (a `search(query, k=5)` returning ranked chunks with source URLs and cosine distances).
- *What it produced:* working scripts using the model named in my spec (`bge-small-en-v1.5`) with ChromaDB and a clean `search()`.
- *What I changed, overrode, or directed differently:* I **overrode the embedding model** to `nomic-embed-text-v1.5`. While verifying, I realized bge-small's 512-token window would silently truncate my 500–800-token guide chunks at embedding time — violating my own chunk ≤ window constraint. I directed it to switch to nomic (8192-token window) and to apply nomic's required `search_document:` / `search_query:` prefixes plus L2-normalization, which the first version omitted. I then updated `planning.md` so the spec matched the code.

**Instance 3 — Grounded generation + interface (Milestone 5)**

- *What I asked the AI to do:* using the Architecture diagram, the retrieval output format, my explicit grounding requirement ("answer from retrieved context only; cite sources; refuse if the answer isn't present"), and a Gradio skeleton, build the RAG loop (`generate.py`) and a web interface (`app.py`).
- *What it produced:* a first version with a working `generate.py` RAG loop and a Gradio app that rendered answer and sources as Markdown components and hid the sources panel on refusal.
- *What I changed, overrode, or directed differently:* (1) I rejected the first UI draft and **redirected it to the simpler skeleton** — plain `Textbox` outputs with a dedicated "Retrieved from" box — and insisted that **source attribution be built programmatically from retrieval metadata**, not left to the LLM. (2) I tightened the grounding test by having it add an **out-of-domain control query** ("best pizza topping?") and confirm the system emits the exact refusal sentence with no sources. (3) When Gradio failed to import, I diagnosed that my local `chunk.py` was shadowing Python's stdlib `chunk` module (via `pydub → wave`) and directed a rename to `chunking.py` rather than accepting a fragile `sys.path` workaround.
