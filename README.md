# educore-analytics

Python service that analyzes student answers to detect learning gaps and generate teacher recommendations.

EduCore Analytics is a companion service that reads student test-attempt data from
[EduCore](https://github.com/ZhurAlex/educore) — every answer type, not just long-text
ones — identifies recurring learning gaps (grammar, vocabulary, verb tenses, etc.), and
generates actionable recommendations for teachers, both at the individual student level
and across the whole class. For each identified gap, it also retrieves matching
exercises from an indexed textbook and recommends the one that best fits.

## How it works

A small server-rendered web UI (no separate frontend, just Jinja2 + FastAPI) walks
you through:

1. **Home** (`/`) — pick a school class.
2. **Class page** — pick analysis type (by student or by test), subject, and language.
3. **Student/test list** — pick who or what to analyze.
4. **Result** — the identified gaps, each with a recommended exercise (click its
   number to expand the full text) and a collapsible list of other candidates.

Two analysis flows, both going through the same pipeline:
- **Per student** — one student's history for one subject: recurring mistakes, and
  topics that were learned then forgotten.
- **Per class/test** — one test, whole class: which questions/topics the class
  struggled with most.

Under the hood, each request runs:

1. **Gap analysis** — an LLM (Gemini, falling back to Mistral, then OpenAI) reads the
   student's/class's answer history and returns a structured list of identified gaps.
2. **Retrieval** — for each gap, its topic is embedded and matched against a
   textbook's exercises (indexed in Postgres + pgvector) using two independent
   similarity searches (by exercise summary and by sub-topic) combined via weighted
   Reciprocal Rank Fusion.
3. **Recommendation** — a second LLM pass picks the single best-matching exercise per
   gap from the retrieved candidates (never inventing one), which gets rendered to
   the teacher alongside the rest as alternatives.

## Setup

```bash
poetry install

cp .env.example .env
# fill in EDUCORE_HOST, EDUCORE_API_KEY (shared secret with educore's ANALYTICS_API_KEY),
# GEMINI_API_KEY, MISTRAL_API_KEY, OPENAI_API_KEY, and the POSTGRES_* vars

docker compose up -d                  # starts Postgres (pgvector/pgvector image)
poetry run alembic upgrade head       # creates the chapters/exercises tables

poetry run uvicorn app.main:app --reload
```

Textbook indexing (populating the `chapters`/`exercises` tables a recommendation is
retrieved from) is a separate, one-off step via the scripts in `scripts/` — not part
of the web app itself.

## Testing

No real API keys needed — `tests/conftest.py` loads `.env.test` (dummy values,
committed to the repo) before any app module is imported, so tests never touch the
real `.env` or burn real Gemini/Mistral/OpenAI tokens, and never hit the real database.

```bash
poetry run pytest                                  # run the suite

poetry run pytest --cov=app --cov-report=html       # with coverage
poetry run python -m http.server 8080 --directory htmlcov
# then open http://localhost:8080/ — NOT the file directly (double-click / file://
# via xdg-open): the report is a set of HTML files linking to each other, and
# opening a single one through the OS file-open dialog sandboxes access to just
# that one file, breaking every link between pages
```

## Tech stack

- **Python 3.13**, [Poetry](https://python-poetry.org/) for dependency management
- [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/)
- [LangChain](https://python.langchain.com/) — structured LLM output and
  provider fallback (Gemini → Mistral → OpenAI, via
  [langchain-google-genai](https://github.com/langchain-ai/langchain-google-genai)/
  [langchain-mistralai](https://pypi.org/project/langchain-mistralai/)/
  [langchain-openai](https://github.com/langchain-ai/langchain-openai))
- [Postgres](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) — stores
  indexed textbook exercises and their embeddings; [SQLAlchemy](https://www.sqlalchemy.org/) (async) +
  [Alembic](https://alembic.sqlalchemy.org/) for the ORM/migrations
- [httpx](https://www.python-httpx.org/) — async client for `educore`'s API
- [Jinja2](https://jinja.palletsprojects.com/) — server-rendered HTML, no separate frontend,
  plain auto-escaping (no markdown/sanitizing step — LLM output is structured data, not free text)
- [ruff](https://docs.astral.sh/ruff/) for linting/formatting, checked in CI
- [pytest](https://docs.pytest.org/) + pytest-asyncio + pytest-cov for testing, checked in CI
