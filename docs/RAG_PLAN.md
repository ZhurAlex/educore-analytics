# RAG-based homework generation — implementation plan

Stage 5 of the project (see `../educore/README.md`'s roadmap): use identified
learning gaps (Stage 4, already built) to retrieve relevant textbook sections
and generate personalized homework. This doc captures the plan before writing
code — decisions here are scoped to this project's actual size (one teacher,
a handful of textbooks), not generic large-scale RAG best practices.

Revised after actually running Stage 1 end-to-end on two textbooks and working
through LangChain's "RAG From Scratch" series — several original assumptions
below turned out wrong in practice; this version reflects what worked.

## Why persistence lives here, not in `educore`

Textbooks/chunks/embeddings are data belonging to the analysis domain, not the
student-testing domain `educore` owns — and `educore`'s own `CLAUDE.md`
explicitly says it shouldn't grow in scope. See `CLAUDE.md`'s architecture
section for the stateless-vs-persistent tradeoff this introduces.

**Stack:** Postgres + `pgvector` (not a dedicated vector DB — unnecessary at
this scale, and one engine for relational + vector data avoids a second
infrastructure component). **LangChain** for the RAG-specific plumbing
(`langchain-postgres`'s `PGVector` vectorstore, `langchain-google-genai` for
embeddings/chat) — a deliberate choice for this feature specifically, not a
project-wide migration: `app/providers.py` (Gemini/Mistral for gap analysis)
stays hand-rolled as-is, since it already works and LangChain buys nothing
there. No Redis/job queue — textbook uploads are rare enough that FastAPI's
`BackgroundTasks` is enough if synchronous processing turns out too slow.

## Stage 1 — PDF extraction

**Reality turned out messier than planned.** `PyMuPDF4LLM` alone garbles
reading order on genuinely multi-column layouts — not just decorative
sidebars, but plain two-column exercise lists — producing word-order-scrambled
text, not just cosmetic noise. `Marker` (with GPU) fixed *ordinary*
multi-column reading order, but did **not** fix implied-pairing matching
exercises (numbered list ↔ lettered list with no explicit link) — that's a
harder, structurally different problem no layout parser we tried solves.
Marker without a GPU is impractical: its OCR backend spawns `llama-server`
(`llama.cpp`) and reliably hits request timeouts on CPU.

Worth trying before reaching for Marker+GPU again: `langchain-pymupdf4llm`
(≥1.28.0 claims improved multi-column reading-order reconstruction and
"smart OCR") and `langchain-pymupdf-layout` (AI-based layout analysis,
**CPU-only** — avoids the GPU/llama.cpp dependency entirely). Untested by us
so far; evaluate on a fresh book before defaulting to Marker.

**Heading/structure detection is unreliable regardless of parser.** Even on
the Marker+GPU run, ~130 of 567 exercise headings (`## Упражнение N`) came out
either wrong heading-level or glued directly onto the exercise text with no
separating whitespace. A regex-based post-processing pass
(`scripts/normalize_exercise_headings.py`, not committed — book-specific, not
reusable) recovered all but ~60: those exercise numbers are **not present
anywhere in the extracted text at all** (OCR skipped them outright), evenly
split between genuinely missing pages in the source PDF (unrecoverable) and
exercises whose number OCR just dropped (their content survived, merged into
the previous exercise's chunk). Budget for a similar per-book cleanup pass
each time a new textbook is ingested — don't expect clean structure "for
free" from any of these parsers.

**Multimodal Vision-LLM (Gemini) is the fallback for pages no text parser
handles** (matching exercises, badly garbled OCR) — cheap enough at this
project's volume (roughly $0.20 per 100 pages at Gemini 2.5 Flash pricing,
comfortably inside the free tier for occasional use) that cost isn't the
constraint. The constraint is *when* to pay it — see Stage 3: don't
pre-process every suspect page up front, do it lazily, only for exercises
that actually get retrieved.

**Page number per exercise is now a hard requirement**, not a nice-to-have —
Stage 3's lazy re-extraction needs to know which PDF page to render and send
to Vision. Not yet implemented in the current parsed output; needs either
`pymupdf4llm`'s `page_chunks=True` (returns per-page dicts instead of one
markdown blob) or equivalent per-page tracking in whichever parser is used.

## Stage 2 — Chunking

Chunk by **document structure**: one chunk = one exercise, boundary = the
(normalized) `## Упражнение N` heading. Fixed-size chunking risks splitting
an exercise's prompt from its answer options mid-way — a correctness bug, not
just a quality tradeoff.

Books can have up to **three** structural levels, not two: book → chapter
(`# АРТИКЛЬ`, always present, reliably extracted) → occasionally a sub-topic
(`### Будущее в прошедшем`, `### SHOULD` — present in some chapters, absent
in most). Capture the sub-topic as metadata when present, fall back to the
chapter name otherwise — don't require it.

The chunker must tolerate the gaps described in Stage 1: exercise numbers
with no recoverable heading (skip, or merge into the neighboring chunk — pick
one and document it, don't silently drop content) and page ranges genuinely
absent from the source PDF.

## Stage 3 — Embeddings & storage

**Don't embed the raw parsed exercise text directly** — it's noisy (OCR
artifacts, bare sentence lists with little inherent topical signal beyond
"grammar drill") and, per Stage 1, sometimes structurally broken. Instead,
follow the **multi-representation indexing** pattern (LangChain's
`MultiVectorRetriever` shape, adapted):

1. For each chunk, use `with_structured_output` (Gemini via
   `langchain-google-genai`) to produce a small Pydantic record: `topic`,
   `sub_topic` (optional), `task_type` (translate / fill-the-gap /
   open-the-brackets / match / etc.), a short **specific** LLM-written
   description of what this exercise actually practices (not just the
   category — needed so retrieval can tell apart the 30+ exercises that
   might share the same `topic`), plus `exercise_num`, `page_number(s)`,
   `book_title`.
2. **Embed the description**, not the raw exercise text — store it via
   `PGVector` (`langchain-postgres`) with the Pydantic fields as metadata
   columns alongside the vector, same rationale as before: relational
   filtering and vector search in one query, one engine.
3. Store the **full exercise text separately**, in a nullable `full_text`
   column — initially whatever Stage 1's parser produced (best-effort, may
   be empty/wrong for known-broken pages).
4. **Lazily backfill `full_text`** the first time a chunk is actually
   retrieved and its stored text is missing or flagged low-confidence: render
   that PDF page (via the page number from Stage 1/2) and re-OCR it through
   Gemini Vision, then persist the result so later retrievals of the same
   exercise reuse it instead of paying for Vision again — a cache-aside
   pattern, not a request-time dependency for exercises that never get used.

## Stage 4 — Retrieval

**Plain dense vector search stays the default**
(`PGVector`'s retriever, `ORDER BY embedding <-> query_embedding LIMIT k`,
filtered by `subject`/`topic`/whatever metadata is available) — no hybrid
search, no reranking, at first.

Evaluated against LangChain's "RAG From Scratch" series and **deliberately
not adopted** at this stage, because none of them fit this project's shape
(a small, curated, single-purpose corpus and a structured, non-ambiguous
query, not an arbitrary user-typed question against a huge noisy corpus):
Multi-Query, RAG-Fusion, Step-Back, HyDE, Query Structuring, Routing, RAPTOR,
ColBERT, CRAG (its web-search fallback actively conflicts with "use only the
provided material"), Adaptive RAG. Revisit any of these **only if retrieval
quality turns out to be a real problem in practice** — not preemptively.

**Decomposition is the one technique actually used, and it's free.** The
query isn't free-form user text needing an LLM call to decompose — it's
already the structured list of gaps that `analyse_student`/`analyse_class`
produce. One retrieval call per identified gap, results combined; no
decomposition prompt needed because the input was never a single blob to
begin with.

## Stage 5 — Prompting

Same shape as the existing prompts in `app/prompts.py`
(`STUDENT_GAP_ANALYSIS_PROMPT`/`CLASS_GAP_ANALYSIS_PROMPT`): role, the
student's context (identified gaps), the retrieved exercises, and an explicit
constraint to use only the provided material — no inventing exercises.
Retrieved candidates carry `book_title`/`chapter`/`exercise_num`/`page` as
structured metadata for citation. Generation reads each candidate's
`full_text` (triggering the Stage 3 lazy Vision fetch first if it's still
empty), not the embedded summary — the summary is a search index, not
generation content.

## Open questions / not yet decided

- Where textbooks get uploaded from (a UI page, vs. a one-off CLI script for
  personal use) — deferred until the ingestion pipeline itself works.
- One parsed file has a `# Contents` heading near the very end (possibly the
  book's real table of contents) — not yet inspected; could turn into a
  ready-made chapter/page outline instead of inferring it from in-body
  headings, worth checking before doing that work by hand.
- Whether the sub-topic (level-3 heading) extraction from Stage 2 is worth
  the per-book effort, or whether chapter-level topic metadata alone is
  good enough in practice — no evidence yet either way.
