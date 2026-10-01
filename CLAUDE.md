# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python service that analyzes student answers from EduCore (a Rails app) — **all answer
types**, not just `long_text`; a wrong `multiple_choice` option or a wrong `short_text`
answer carries the same kind of signal as a `long_text` mistake — to detect learning
gaps (grammar, vocabulary, verb tense, etc.) and generate teacher-facing
recommendations, per student and per class. See `README.md` for the one-paragraph pitch.

**Status: MVP working end-to-end.** FastAPI service, stateless — no database; every
request re-reads from `educore`'s API, nothing persisted here. A server-rendered web UI
(Jinja2, no separate frontend build) walks a teacher through class → analysis type →
student/test → result; the result calls an LLM (Gemini, falling back to Mistral) and
renders the markdown recommendation as HTML.

**In progress:** RAG-based homework generation (uses identified gaps to retrieve
relevant textbook sections and generate personalized homework) — the first feature that
needs persistence (Postgres + `pgvector`, breaking the stateless design above on
purpose). Plan: `docs/RAG_PLAN.md`.

## Commands

```bash
poetry install                        # install deps (+ dev group: ruff)
                                       # fill in .env: EDUCORE_HOST, EDUCORE_API_KEY,
                                       # GEMINI_API_KEY, MISTRAL_API_KEY — settings.py
                                       # fails fast at import time if any is missing

poetry run uvicorn app.main:app --reload  # dev server, localhost:8000, auto-reload
poetry run python -m app.main             # same, no reload — NOT `python app/main.py`:
                                           # that runs it outside the `app` package, so
                                           # the absolute imports (`from app.X import Y`)
                                           # can't resolve

poetry run ruff check .               # lint — same check CI runs
poetry run ruff check --fix .         # autofix what's fixable
poetry run ruff format .              # format
poetry run ruff format --check .      # format check — same as CI

poetry run pytest                     # run the test suite — same as CI
poetry run pytest --cov=app --cov-report=html   # with HTML coverage report;
                                       # open via `python -m http.server --directory
                                       # htmlcov`, not a raw file:// URL — the report's
                                       # inter-page links break under the OS's
                                       # single-file sandboxed file-open
```

## Architecture

All application modules live under `app/` (a plain package — `python -m app.main` or
`uvicorn app.main:app`, not `python app/main.py`, which runs outside the package and
breaks the absolute imports below). Tests live in a separate top-level `tests/`,
mirroring this layout (`tests/test_<module>.py` per `app/<module>.py`).

### Request flow

`app/routes.py` renders a page flow, no JSON API surface — every route returns HTML
via `Jinja2Templates` (`app/templates/`), no `response_class` overrides needed since
`TemplateResponse` is returned directly:

1. `GET /` — list of school classes (`classes.html`), from `fetch_classes()`.
2. `GET /classes/{class_id}` — pick analysis type + `subject` + `language`
   (`analysis_configuration.html`): one `<form method="get">` with two submit buttons,
   each carrying a different `formaction` (`/class/{id}/students` or
   `/class/{id}/tests`) — the `<select>` values ride along as query params on
   whichever button was clicked, no JS needed.
3. `GET /class/{class_id}/students` / `GET /class/{class_id}/tests` — list of
   students/tests for that class (`students.html`/`tests.html`), `subject`/`language`
   threaded through as query params to the next step's links.
4. `GET /students/{student_id}/gap-analysis` / `GET /class/{test_id}/class-analysis` —
   runs the actual analysis. Shared by `render_analysis()`: empty `responses` →
   `no_results.html`; otherwise calls the given `analyse_student`/`analyse_class`
   function, converts the LLM's markdown reply to HTML (`markdown.markdown()`), then
   **sanitizes it** through `bleach.clean()` (allow-list of tags/attributes,
   `ALLOWED_RESULT_TAGS`/`ALLOWED_RESULT_ATTRIBUTES` in `routes.py`) before rendering
   `analysis_results.html` with `{{ result_html | safe }}`. The sanitizing step matters
   because the LLM's reply isn't trusted content — its prompt is built from student
   answer text (`formatting.py`), so a student could type something that gets echoed
   back into the LLM's output and, without sanitizing, rendered as live HTML/JS in a
   teacher's browser. `| safe` opts out of Jinja2's default auto-escaping — safe here
   specifically because `bleach.clean()` already ran, not because the content is
   inherently trustworthy.

`get_students_attempts`/`get_class_attempts` differ only in which `fetch_attempts`
filters and which `analyse_*` function to call — `render_analysis()` takes the
analyse function as a plain argument (functions are first-class values) rather than
duplicating the fetch → empty-check → analyse → render sequence twice.

### Module boundaries

- **`educore_client.py`** — the only place that speaks HTTP to `educore`'s API:
  `fetch_test_attempts`, `fetch_classes`, `fetch_students`, `fetch_tests`, all thin
  wrappers around a shared `make_request(url, params=None)` (note the `None` default,
  not `{}` — a mutable default arg would be shared across every call that doesn't pass
  one). Deliberately has no FastAPI import — raises plain `httpx` exceptions rather
  than `HTTPException`, so it isn't tied to this web framework and could be reused
  outside it. `routes.py` is where those exceptions get translated into HTTP responses.
- **`app/templates/`** (Jinja2) — `base.html` holds the shared `<head>`/layout;
  every page template does `{% extends "base.html" %}` and fills `content`/`title`
  blocks, so no page repeats boilerplate markup. `app/static/style.css` is mounted at
  `/static` in `main.py`.
- **`formatting.py`** — turns the raw JSON from `educore` into the plain-text blob that
  goes into the LLM prompt. Two independent paths:
  - `format_student_responses` — chronological, includes **every** response (not just
    wrong ones), because there's no topic/skill tag on `Question` to group by — the LLM
    needs to see the full pattern (e.g. 5 correct + 1 wrong on the same grammar point)
    to tell a recurring gap from a one-off slip.
  - `format_class_responses` — groups by question text across every student who took
    that test, and pre-aggregates (wrong count / total, most common wrong answers via
    `Counter`) in code rather than handing the LLM a raw per-student dump — keeps the
    numeric ranking deterministic and the prompt short.
  - Both exclude `pending`/`manual_check_required` responses (`IGNORED_GRADING_STATUSES`)
    — ungraded or failed-grading data shouldn't feed the analysis.
- **`prompts.py`** — the two system prompt templates (`STUDENT_GAP_ANALYSIS_PROMPT`,
  `CLASS_GAP_ANALYSIS_PROMPT`), parameterized by `{subject}`/`{language}` rather than a
  cartesian list of pre-written personas per subject.
- **`providers.py`** — the LLM layer, ported from `../TeacherBot`'s ports-and-adapters
  design: `LLMProvider` (port) with `GeminiProvider`/`MistralProvider` (adapters) and
  `FallbackProvider` (tries Gemini, falls back to Mistral on failure). Fully async.
- **`analysis.py`** — orchestrates one analysis call: format → fill prompt template →
  `provider.generate()`. `subject`/`language` are real parameters here, not hardcoded.
- **`settings.py`** — loads `.env` once and validates every required var is present at
  import time (raises immediately, not deep inside some later HTTP call).

### Tests

- **`tests/conftest.py`** — loads `.env.test` (dummy values, safe to commit) with
  `override=True` before any test module is collected/imported. Since `settings.py`
  reads env vars at import time, this must run before `app.settings` is ever pulled in
  by a test — otherwise a test could silently load the real `.env` and hit real
  Gemini/Mistral/educore APIs with real credentials. `load_dotenv`'s default
  `override=False` means this only works because `conftest.py` sets the dummy values
  *first*, before `settings.py` gets a chance to load the real ones.
- **`tests/fixtures/`** — shared parametrize data (e.g. `formatting_cases.py`), kept
  out of `tests/` itself so plain `test_*.py` files stay easy to pick out from a
  directory listing.
- Provider tests (`GeminiProvider`/`MistralProvider`) patch the SDK client classes
  where they're *imported* (`app.providers.Mistral`), not where they're *defined*
  (`mistralai.client.Mistral`) — `from x import Y` binds a separate name in the
  importing module, so patching the original definition doesn't affect it.
- `FallbackProvider` tests use a hand-written `FakeProvider(LLMProvider)` instead of
  mocking Gemini/Mistral — it only depends on the `LLMProvider` interface, so no SDK
  mocking is needed to test its retry/fallback logic.

## Companion project: `../educore`

The Rails app this service reads from. Full schema/architecture:
`../educore/docs/SPEC.md` and `../educore/CLAUDE.md`.

Relevant pieces for this project specifically:

- `Question` — `answer_type` (`multiple_choice`/`short_text`/`long_text`),
  `correct_answer` (for `long_text`: a reference answer/rubric passed to Gemini, not a
  string it's compared against verbatim the way it is for `short_text`; the API hands
  this back per response as `correct_answer`, already resolved to the right
  `Option#body` for `multiple_choice` — no need to join options yourself)
- `Response` — one per (attempt, question), for **every** answer type, not just
  `long_text`: `answer_text` (`short_text`/`long_text`) or `option_id`
  (`multiple_choice`), `points_awarded`, `feedback` (only ever populated for `long_text` —
  Gemini's explanation, or a teacher's own note; `nil` for the other two types),
  `grading_status` (`auto_graded`/`teacher_overridden`/`pending`/`llm_graded`/
  `manual_check_required` — the last one means Gemini grading failed and a teacher
  hasn't reviewed it yet, worth excluding or flagging separately in any analysis)
- `TestAttempt` — `student_id`, `test_id`, `status`
  (`in_progress`/`evaluating`/`completed`), `score`, `grade`, `started_at`
- `Student`/`SchoolClass` — for grouping detected error patterns per student and per class

**Data access: via API, built.** `GET /api/test_attempts` (filterable by
`test_id`/`student_id`/`school_class_id`/`subject`), plus three lookup endpoints that
back this project's own UI — `GET /api/school_classes`, `GET /api/tests`,
`GET /api/students` (the latter two take an optional `school_class_id` filter, for the
class → tests/students cascade in `routes.py`). `GET /api/tests?school_class_id=X`
returns tests *assigned* to the class (`Test#for_school_class`, via
`test_assignments`), not only tests actually attempted — a deliberate choice on the
`educore` side, not a bug to route around here. Token auth (`Authorization: Bearer
<token>` — the same secret value must be set in both projects' env; `educore` calls it
`ANALYTICS_API_KEY`, this project stores it as `EDUCORE_API_KEY` in
`.env`/`settings.py`).
Full contract, including the exact response shape and known gaps (no pagination, no
versioning yet):

@../educore/docs/API_CONTRACT.md
