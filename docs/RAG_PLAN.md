# RAG-based homework generation — implementation plan

Stage 5 of the project (see `../educore/README.md`'s roadmap): use identified
learning gaps (Stage 4, already built) to retrieve relevant textbook sections
and generate personalized homework. This doc captures the plan before writing
code — decisions here are scoped to this project's actual size (one teacher,
a handful of textbooks), not generic large-scale RAG best practices.

## Why persistence lives here, not in `educore`

Textbooks/chunks/embeddings are data belonging to the analysis domain, not the
student-testing domain `educore` owns — and `educore`'s own `CLAUDE.md`
explicitly says it shouldn't grow in scope. See `CLAUDE.md`'s architecture
section for the stateless-vs-persistent tradeoff this introduces.

**Stack, already decided:** Postgres + `pgvector` (not a dedicated vector DB —
unnecessary at this scale, and one engine for relational + vector data avoids
a second infrastructure component) + SQLAlchemy + Alembic (matches
`../TeacherBot`'s existing stack, extended with `pgvector`'s SQLAlchemy type).
No Redis/job queue — textbook uploads are rare enough that FastAPI's
`BackgroundTasks` is enough if synchronous processing turns out too slow.

## Stage 1 — PDF extraction

**`PyMuPDF4LLM`** as the default: lightweight, no GPU/separate service
needed (unlike `Marker`), outputs Markdown directly — which this project
already has tooling for (`python-markdown` + `bleach`, from the analysis
results pipeline). Naive text extraction (`pypdf`/`pdfplumber`) loses table
structure and merges headings into body text — not viable for textbooks with
exercises/tables. Multimodal OCR (Docling, GPT-4o-mini-style) is a fallback
for specific pages `PyMuPDF4LLM` mangles, not the default — expensive at
volume, unnecessary for most pages.

## Stage 2 — Chunking

Chunk by **document structure** (heading/exercise-number boundaries in the
Markdown output), not fixed-size windows. Fixed-size chunking risks splitting
an exercise's prompt from its answer options mid-way — a correctness bug, not
just a quality tradeoff, for a feature whose whole point is retrieving intact
exercises. Since `PyMuPDF4LLM` already preserves heading hierarchy in its
Markdown output, this can be regex/structure-based per book rather than
needing a dedicated semantic-chunking library.

## Stage 3 — Embeddings & storage

- **Embeddings: Gemini's embeddings API** — reuses the already-configured
  Gemini provider/credentials instead of adding a third LLM-adjacent
  dependency (no new API key, no local model weights to manage).
- **Storage: Postgres + `pgvector`**, per the companion-project decision
  above. Metadata (`book_title`, `chapter`, `topic`, `exercise_num`) as
  regular columns alongside the vector column — not something extra bolted
  on, this is the actual reason `pgvector` was chosen over a dedicated
  vector DB: relational filtering and vector search in one query, one engine.

## Stage 4 — Retrieval

**Start with plain dense vector search** (`pgvector` cosine/L2 distance,
`ORDER BY embedding <-> query_embedding LIMIT k`, filtered by `subject` and
whatever metadata columns are available) — no hybrid search (dense + BM25)
and no reranking step at first.

Hybrid search + reranking is standard advice for RAG at scale — where dense
search alone starts returning too many plausible-but-wrong candidates across
a large, ambiguous corpus. At this project's actual scale (a handful of
textbooks, likely hundreds to low thousands of chunks total, not millions),
that failure mode is unlikely to show up. Add hybrid search/reranking later
**only if retrieval quality turns out to be a real problem in practice** —
not preemptively.

## Stage 5 — Prompting

Same shape as the existing prompts in `app/prompts.py`
(`STUDENT_GAP_ANALYSIS_PROMPT`/`CLASS_GAP_ANALYSIS_PROMPT`): role, the
student's context (identified gaps), the retrieved exercises (with
book/chapter/exercise-number references), and an explicit constraint to use
only the provided material — no inventing exercises. Parameterized template,
not hardcoded per subject/language, following the existing convention.

## Open questions / not yet decided

- Where textbooks get uploaded from (a UI page, vs. a one-off CLI script for
  personal use) — deferred until the ingestion pipeline itself works.
- Exact chunking regex/structure per book — likely needs hand-tuning per
  textbook given the small number of books involved, not a fully generic
  parser.
