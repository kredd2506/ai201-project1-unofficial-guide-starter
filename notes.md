# Project Journal — The Unofficial Guide (Project 1)

> Running log of decisions, learnings, and pivots. Newest entries on top.

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
