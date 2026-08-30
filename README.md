# educore-analytics

Python service that analyzes student answers to detect learning gaps and generate teacher recommendations.

EduCore Analytics is a companion service that reads student test-attempt data from
[EduCore](https://github.com/ZhurAlex/educore) — every answer type, not just long-text
ones — identifies recurring learning gaps (grammar, vocabulary, verb tenses, etc.), and
generates actionable recommendations for teachers, both at the individual student level
and across the whole class.

## Endpoints

- `GET /students/{student_id}/gap-analysis?subject=...` — one student's history for one
  subject: recurring mistakes, and topics that were learned then forgotten.
- `GET /class/{test_id}/class-analysis?school_class_id=...` — one test, whole class:
  which questions/topics the class struggled with most.

Both return a plain-text recommendation, not JSON.

## Setup

```bash
poetry install

cp .env.example .env
# fill in EDUCORE_HOST, EDUCORE_API_KEY (shared secret with educore's ANALYTICS_API_KEY),
# GEMINI_API_KEY, MISTRAL_API_KEY

poetry run uvicorn app.main:app --reload
```

## Testing

No real API keys needed — `tests/conftest.py` loads `.env.test` (dummy values,
committed to the repo) before any app module is imported, so tests never touch the
real `.env` or burn real Gemini/Mistral tokens.

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

- **Python 3.14**, [Poetry](https://python-poetry.org/) for dependency management
- [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/)
- [google-genai](https://github.com/googleapis/python-genai) / [mistralai](https://github.com/mistralai/client-python) — LLM providers, Gemini first with a Mistral fallback
- [httpx](https://www.python-httpx.org/) — async client for `educore`'s API
- [ruff](https://docs.astral.sh/ruff/) for linting/formatting, checked in CI
- [pytest](https://docs.pytest.org/) + pytest-asyncio + pytest-cov for testing, checked in CI
