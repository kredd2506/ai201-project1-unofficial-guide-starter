# Sources — GT CS Unofficial Guide

## Domain
CS course and professor reviews at Georgia Tech — workload, grading, teaching quality, and degree requirements. This knowledge is scattered across review sites, grade-data tools, and unofficial student aggregators; there's no single place to ask "which Algorithms professor is clearest?" or "what's the real workload for CS 6601?" Official catalog pages tell you *what* a course is, not *what it's like*.

> **All 10 URLs verified live on 2026-06-07.**

---

## Source List

### Rate My Professors (short reviews — opinion)
| # | Description | URL | Status |
|---|-------------|-----|--------|
| 1 | All GT professors; difficulty, grading, workload | https://www.ratemyprofessors.com/search/professors/361?q=* | ✅ live (2,975 profs, "Georgia Institute of Technology") |
| 2 | GT school landing page; browse/filter by department | https://www.ratemyprofessors.com/school/361 | ✅ live |

> **Skim notes:** Reviews are 2–5 sentences, very high signal-to-noise. Key info (difficulty, grade fairness, workload) usually in the first 1–2 sentences. → **Short chunks; one chunk per review.**
> **Note:** The old `?did=361` "Math department" URL was broken (361 is the *school* id, not a department id — it returned drafting profs at other schools) and was removed. RMP's department filter is in-page/stateful and doesn't map cleanly to a stable URL.

---

### Structured course & section data (facts)
| # | Description | URL | Status |
|---|-------------|-----|--------|
| 3 | GT Scheduler crawler — per-term course/section/instructor JSON | https://gt-scheduler.github.io/crawler-v2/index.json (per-term files, e.g. `202402.json`) | ✅ live (terms 2020–2024+) |
| 6 | GT MATH undergraduate catalog — descriptions, credit hours | https://catalog.gatech.edu/courses-undergrad/math/ | ✅ live |
| 8 | GT CS undergraduate catalog — descriptions, prereqs, credit hours | https://catalog.gatech.edu/courses-undergrad/cs/ | ✅ live (2026–27) |
| 9 | GT CS BS degree requirements — core/elective + Threads | https://catalog.gatech.edu/programs/computer-science-bs/ | ✅ live (124 cr, Threads model) |
| 10 | GT OMSCS official current courses (online grad) | https://omscs.gatech.edu/current-courses | ✅ live (60+ courses) |

> **Skim notes:** Very structured, short factual entries. Prereq chains and which-instructor-teaches-which-section are important context. → **Chunk by course/section entry; keep title + number + prereqs (and instructor) together.** GT Scheduler data is JSON — parse, don't naively text-chunk.

---

### Course reviews with difficulty/workload metrics (opinion + data)
| # | Description | URL | Status |
|---|-------------|-----|--------|
| 4 | OMSHub — OMSCS per-term review dataset (text + difficulty + workload hours) | https://github.com/omshub/data/tree/main/data (e.g. `data/202402.json`) | ✅ live (raw JSON, 2014→present) |
| 5 | OMSCentral — OMSCS course reviews (second aggregator) | https://www.omscentral.com/courses | ✅ live (JS SPA — data via its API, not the rendered page) |

> **Skim notes:** Each review pairs free-text with numeric difficulty/workload ratings. Reviews vary from one line to several paragraphs. → **Chunk per review; carry difficulty/workload-hours and course id as metadata.** #5 renders client-side, so ingest from its API/data, not by scraping HTML.

---

### Grade data (numeric)
| # | Description | URL | Status |
|---|-------------|-----|--------|
| 7 | GT Course Critique (Oscar) — grade distributions / GPA by prof & section | https://critique.gatech.edu | ✅ live |

> **Skim notes:** Quantitative — GPA, A/B/C/withdraw rates per professor/section. → **One structured record per professor-course-section; store as metadata-rich rows, not prose chunks.**

---

## Dropped source — Reddit (r/gatech)
Reddit was the original plan for undergrad discussion (course advice, "is X good to pair with Y", workload threads) but was **dropped**: every Reddit endpoint (`www`, `old`, and the `.json` API) returns **HTTP 403** to unauthenticated requests, so it can't be fetched or ingested without the official Reddit API (PRAW + a registered OAuth app) or manual copy-paste into local files. Revisit via PRAW or local saves if undergrad community discussion proves to be a coverage gap.

---

## Coverage Check — 5 Questions This System Should Answer
(Full versions with expected-answer targets live in `planning.md` → Evaluation Plan.)
1. For CS 3510 (Algorithms), which professor is rated clearest, and how do their grades compare? → #1, #2, #3, #7
2. What's the weekly workload (hours) and difficulty for CS 6601 (AI)? → #4, #5, #10
3. What do students say about David Joyner's teaching/grading style? → #1, #4, #5
4. What are the prerequisites and credit hours for CS 4641 (Machine Learning)? → #8, #9
5. Which MATH courses are required for the CS BS, and what do they cover? → #6, #9

---

## Notes for Milestone 2 (Chunking)
- **RMP reviews (#1–2)** → one chunk per review (short, self-contained).
- **Catalog / degree / OMSCS pages (#6, #8, #9, #10)** → one chunk per course entry; keep prereqs in the same chunk.
- **GT Scheduler JSON (#3)** → parse JSON; one entry per course-section with instructor as metadata.
- **OMSHub / OMSCentral reviews (#4–5)** → one chunk per review; attach difficulty + workload-hours + course id as metadata.
- **Course Critique (#7)** → structured records, not prose; one per prof-course-section.
