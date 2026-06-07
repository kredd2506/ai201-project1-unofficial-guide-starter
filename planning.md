# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

This system covers student reviews of CS courses and professors at Georgia Tech — workload, grading difficulty, teaching quality, and degree planning. That knowledge is valuable because official catalog pages describe what a course *is* but never what it's actually like to take — its real workload, whether a professor grades fairly, or which section to pick. And because that experience lives scattered across Rate My Professors, grade-distribution tools, and unofficial student aggregators, there's no single place to ask questions like "which Algorithms professor is clearest?" or "is CS 3600 too heavy to pair with OS?"

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors — GT professors | All GT professors; difficulty, grading, workload reviews | https://www.ratemyprofessors.com/search/professors/361?q=* |
| 2 | Rate My Professors — GT school page | GT landing page; browse/filter reviews by department | https://www.ratemyprofessors.com/school/361 |
| 3 | GT Scheduler — crawler data | Structured per-term course/section/instructor data (who teaches what) | https://gt-scheduler.github.io/crawler-v2/index.json (per-term JSON, e.g. `202402.json`) |
| 4 | OMSHub — OMSCS review dataset | Per-term course reviews with difficulty + workload-hours + written text | https://github.com/omshub/data/tree/main/data (e.g. `data/202402.json`) |
| 5 | OMSCentral — OMSCS course reviews | Second review aggregator; difficulty/workload ratings + reviews | https://www.omscentral.com/courses (JS SPA — ingest via its API) |
| 6 | GT MATH Undergraduate Catalog | Math course descriptions/credit hours (CS-required math: 1554, 2550, 3012…) | https://catalog.gatech.edu/courses-undergrad/math/ |
| 7 | GT Course Critique (Oscar) | Grade distributions / GPA by professor and section | https://critique.gatech.edu |
| 8 | GT CS Undergraduate Catalog | CS course descriptions, prereqs, credit hours | https://catalog.gatech.edu/courses-undergrad/cs/ |
| 9 | GT CS BS Degree Requirements | Core vs. elective breakdown + Threads for the CS BS | https://catalog.gatech.edu/programs/computer-science-bs/ |
| 10 | GT OMSCS — Official Current Courses | Official list/descriptions of online CS graduate courses | https://omscs.gatech.edu/current-courses |

All 10 URLs verified live on 2026-06-07. Reddit (`r/gatech`) was evaluated but dropped: it returns HTTP 403 to unauthenticated fetches, so it can't be ingested without the official API (PRAW + OAuth) or manual saving. See [`sources.md`](./sources.md) for skim notes and per-source chunking implications.

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

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

| # | Question | Expected answer (verifiable target) | Sources |
|---|----------|-------------------------------------|---------|
| 1 | For CS 3510 (Algorithms), which professor do students rate as clearest, and how do their grade outcomes compare? | A named professor backed by RMP "clear/clarity" comments, cross-checked against that prof's Course Critique GPA/grade distribution. *Judge: a specific name + ≥1 cited review + one grade stat.* | #1, #2, #3, #7 |
| 2 | What's the typical weekly workload (hours) and difficulty rating for CS 6601 (AI)? | An aggregated workload figure (~hrs/week) and difficulty score from OMSHub/OMSCentral reviews. *Judge: a numeric workload + difficulty grounded in cited reviews.* | #4, #5, #10 |
| 3 | What do students say about David Joyner's teaching and grading style? | A grounded summary of recurring sentiments (e.g., structure, rubric fairness, responsiveness) with cited reviews. *Judge: ≥2 review-based points, no uncited claims.* | #1, #4, #5 |
| 4 | What are the prerequisites and credit hours for CS 4641 (Machine Learning)? | Credit hours = 3 (catalog-confirmed); prerequisite chain exactly as listed in the GT CS catalog entry. *Judge: matches the ingested catalog entry.* | #8, #9 |
| 5 | Which MATH courses are required for the CS BS, and what do they cover? | The required math sequence from the CS BS degree requirements, plus course descriptions from the MATH catalog. *Judge: course numbers match the degree-requirements source.* | #6, #9 |

> Each question is specific enough to grade right/wrong and is answerable by a named subset of the corpus. Factual values (exact prereqs, the math sequence) are confirmed against the ingested source at evaluation time — the GT catalog stores prereqs in a structured sidebar and the BS requirements on a rendered "Requirements" tab, so they need targeted extraction during ingestion (see notes.md).

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
