# RAG-based homework generation — implementation plan

Stage 5 of the project (see `../educore/README.md`'s roadmap): use identified
learning gaps to retrieve relevant textbook sections and generate personalized
homework. Scoped to this project's actual size — one teacher, a handful of
textbooks — not generic large-scale RAG best practices.

**Status: Stages 1-3 done, data loaded. Stages 4-5 not started.**

## Why persistence lives here, not in `educore`

Textbooks/chunks/embeddings belong to the analysis domain, not the
student-testing domain `educore` owns. See `CLAUDE.md` for the
stateless-vs-persistent tradeoff this introduces.

**Stack:** Postgres + `pgvector` — one engine for relational and vector data,
no separate vector DB needed at this scale. No `langchain-postgres`, no
LangChain vectorstore abstraction — plain SQLAlchemy models instead (see
Stage 3). `app/providers.py` (Gemini/Mistral for gap analysis) stays
hand-rolled as-is; LangChain is used only for this feature.

## Stages 1-3 — extraction, structuring & storage (done)

Two text parsers were tried first and both lost structure: `PyMuPDF4LLM`
scrambled word order on genuinely multi-column exercise lists, and `Marker`
(GPU) fixed ordinary multi-column reading order but still broke ~130 of 567
exercise headings and lost ~60 exercise numbers outright — OCR-level
structure detection turned out to be the hard part, not text extraction.

Sending each chapter PDF straight to a Vision-LLM (Gemini/GPT, via
`create_agent` with a Pydantic `response_format`) solved extraction and
structuring in one step — the model returns typed `Exercise` objects
(`number`, `page`, `task_type`, `text`, `summary`, ...) directly, no separate
chunking pass needed.

Problems hit along the way, each with a different fix:
- **Content-filter false positive** on one exercise (an innocent
  misunderstanding anecdote misread as something darker) — switched that
  chapter to a different provider.
- **Free-tier rate limits** on preview models — resumable `already_processed()`
  skip-list so a retry only redoes the failed chapter.
- **Hallucinated page numbers** on two chapters — the model produced a
  suspiciously perfect sequential run instead of reading the printed page;
  found by scanning all chapters for that statistical fingerprint, fixed by
  rendering and OCR-verifying the real pages.

Storage is plain SQLAlchemy models (`common/models.py`: `Chapter`,
`Exercise`) with an Alembic-managed `pgvector` column
(`embedded_summary: Vector(768)`) — not `langchain-postgres`'s `PGVector`.
Following the multi-representation indexing idea without the framework
abstraction: embed the LLM-written `summary` (specific, low-noise), not the
raw OCR'd exercise text, and keep the full text alongside it for generation.
`scripts/db_saver.py` embeds via `GoogleGenerativeAIEmbeddings`
(`gemini-embedding-2-preview`, dim 768) and loads both tables. 18 chapters,
561 exercises are in Postgres now.

## Stage 4 — Retrieval (not started)

Plain dense vector search (`ORDER BY embedding <-> query_embedding LIMIT k`),
filtered by metadata — no hybrid search, no reranking. Evaluated against
LangChain's "RAG From Scratch" techniques (Multi-Query, RAG-Fusion,
Step-Back, HyDE, Query Structuring, Routing, RAPTOR, ColBERT, CRAG, Adaptive
RAG) and none fit: this is a small curated corpus with a structured,
non-ambiguous query, not free-form user text against a huge noisy one.
Revisit only if retrieval quality is a real problem in practice.

Decomposition is free here: the query is already the structured list of gaps
`analyse_student`/`analyse_class` produce, so one retrieval call per gap,
results combined — no decomposition prompt needed.

## Stage 5 — Prompting (not started)

Same shape as `app/prompts.py`'s existing prompts: role, the student's
identified gaps, the retrieved exercises, an explicit "use only the provided
material" constraint. Retrieved candidates carry `book_title`/`chapter`/
`exercise_num`/`page` for citation, and generation reads each candidate's
full text, not the embedded summary.

## Open questions

- Upload path — UI page vs. one-off CLI script — deferred until retrieval
  proves the pipeline is worth building on.
- One parsed file has a `# Contents` heading near the end, possibly the
  book's real table of contents — unchecked; could replace inferring
  chapter/page structure from in-body headings.
- Whether sub-topic extraction is worth the per-book effort over chapter-level
  topic alone — no evidence yet either way.
