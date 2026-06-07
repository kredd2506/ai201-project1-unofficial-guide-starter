# Notes & Learnings — GT CS Unofficial Guide

> Running log of decisions and gotchas while building the source list / RAG pipeline.

---

## Milestone 1 — Source selection (2026-06-07)

### Key learnings

- **Verify every URL before committing it.** Of the original 10 sources, two were bad:
  - The RMP "GT Math" URL (`?did=361`) was broken — `361` is RateMyProfessors' *school* id for Georgia Tech, **not** a department id. Reusing it as `did` filtered nothing and returned drafting professors at unrelated schools. RMP's department filter is in-page/stateful and doesn't map to a stable URL, so we replaced it with the GT school landing page (`/school/361`).
  - The four Reddit search URLs couldn't be fetched at all (see below).

- **This is RAG over a *local* corpus.** The pipeline reads files from `documents/`, it does not fetch live URLs at query time. So a URL failing in WebFetch is only a *verification* nuisance — what actually matters is whether each source's text can get into `documents/` once. A source is only truly disqualified if it can't be ingested *at all* (which is what killed Reddit).

- **Aim for format diversity, not just 10 links.** The rubric warns against "10 pages that all say the same thing." Final set deliberately spans:
  - short opinion reviews (RMP) → one chunk per review
  - structured JSON section/instructor data (GT Scheduler) → parse, don't text-chunk
  - reviews + numeric difficulty/workload metrics (OMSHub, OMSCentral) → per-review chunk + metadata
  - catalog/degree prose (CS + Math catalog, degree reqs, OMSCS courses) → one chunk per course entry
  - numeric grade distributions (Course Critique) → structured records, not prose
  This directly drives the Milestone 2 chunking strategy.

- **JS single-page apps need their API, not the rendered page.** OMSCentral (and OMSHub's site) load reviews client-side, so a fetcher sees "0 courses." Ingest from the underlying API / data repo instead of scraping HTML. OMSHub conveniently publishes raw per-term review JSON at `github.com/omshub/data`.

- **Coverage caveat to watch:** dropping Reddit shifted course-*experience* opinion toward OMSCS (online grad) sources (#4, #5, #10). Undergrad opinion now rests mainly on RMP (#1, #2) + Course Critique (#7). Revisit if test questions are undergrad-heavy.

- **GT catalog hides the structured fields.** Course *prerequisites* don't appear in the catalog page's body text — they're in a structured sidebar — and the CS BS *degree requirements* (the actual required course list) live on a rendered "Requirements" tab, not the overview prose. A naive HTML-to-text scrape drops both. → Ingestion for #6/#8/#9 needs targeted extraction (the structured prereq field + the requirements tab), not just page-body chunking. This is why evaluation Q4/Q5 mark exact facts as "confirm against ingested source."

### 5 evaluation questions (M1 check)
We can describe 5 specific, gradable questions, each answerable by a named subset of the corpus — so the domain is narrow enough (full versions + expected-answer targets in `planning.md` → Evaluation Plan). Note: "Professor X" placeholder was replaced with a real, heavily-reviewed professor (David Joyner) so the question is concretely testable.

---

## Why we dropped Reddit (r/gatech)

Reddit was the original plan for undergrad community discussion — course advice, "is X good to pair with Y", workload threads — content no other source really replaces.

**It was dropped because it cannot be ingested without authentication:**

- WebFetch is blocked for **every** Reddit domain — `www.reddit.com`, `old.reddit.com`, and the `.json` API endpoint all fail.
- Confirmed it's not just a WebFetch limitation: a plain `curl` with a browser user-agent against the `.json` API returns **HTTP 403 Forbidden**. So unauthenticated programmatic access is blocked at Reddit's end, for the ingestion pipeline too — not just for verification.

**What it would take to use Reddit anyway (deferred, not impossible):**

1. **Official Reddit API (PRAW)** — register a free Reddit OAuth app and pull threads with credentials. Reproducible and scalable, but adds setup + secrets management.
2. **Manual save** — copy a handful of high-value threads into `documents/` as `.md`/`.txt`. Zero API, fully stable and citable for RAG; doesn't scale.

**Decision:** dropped for now and replaced with verified, fetchable, *distinct* sources. Revisit via PRAW or manual saves only if undergrad community discussion proves to be a real coverage gap during evaluation.
