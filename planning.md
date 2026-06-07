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

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
