# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python service that analyzes student answers from EduCore (a Rails app) — **all answer
types**, not just `long_text`; a wrong `multiple_choice` option or a wrong `short_text`
answer carries the same kind of signal as a `long_text` mistake — to detect learning
gaps (grammar, vocabulary, verb tense, etc.) and generate teacher-facing
recommendations, per student and per class. See `README.md` for the one-paragraph pitch.

**Status: MVP working end-to-end**, including a RAG-based homework recommendation
pipeline. FastAPI service with a server-rendered web UI (Jinja2, no separate frontend
build) that walks a teacher through class → analysis type → student/test → result:
gap analysis (Gemini → Mistral → OpenAI fallback, structured output) identifies
learning gaps from the student's/class's answer history, retrieval (Postgres +
`pgvector`, dual-embedding weighted RRF over textbook exercise `summary`/`sub_topic`)
finds matching exercises, and a second LLM pass picks the best match per gap before
rendering the recommendation to the teacher. Persistence (Postgres) was added
specifically for this feature — everything else in the service stays stateless,
re-reading from `educore`'s API on every request.

## Commands

```bash
poetry install                        # install deps (+ dev group: ruff)
                                       # fill in .env: EDUCORE_HOST, EDUCORE_API_KEY,
                                       # GEMINI_API_KEY, MISTRAL_API_KEY, OPENAI_API_KEY,
                                       # POSTGRES_* — settings.py fails fast at import
                                       # time if any of these except OPENAI_API_KEY is
                                       # missing (that one's read directly by LangChain,
                                       # not threaded through settings.py)

docker compose up -d                  # Postgres (pgvector/pgvector image)
poetry run alembic upgrade head       # creates chapters/exercises tables

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
   function (see `analysis.py` below) and renders `analysis_results.html` with the
   resulting `list[FinalRecommendation]`. No markdown rendering or HTML sanitizing
   step — the LLM's output is structured data (Pydantic, not free text) by the time it
   reaches the template, and every field is interpolated through plain `{{ }}` (never
   `| safe`), so Jinja2's default auto-escaping alone is enough to keep student-typed
   text that made it into an LLM reply from being rendered as live HTML/JS in a
   teacher's browser.

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
- **`prompts.py`** — three system prompt templates: `STUDENT_GAP_ANALYSIS_PROMPT`,
  `CLASS_GAP_ANALYSIS_PROMPT` (parameterized by `{subject}`/`{language}` rather than a
  cartesian list of pre-written personas per subject — both instruct the model to
  always write `topic` in English regardless of `{language}`, since it's used to
  search an English-language textbook database, while `description` follows
  `{language}`) and `FIND_RECOMMENDED_EXERCISES_PROMPT` (no `{subject}`/`{language}` —
  it only ever sees already-retrieved exercise text and picks among given ids).
- **`providers.py`** — the LLM layer: a single `make_request_to_LLM(message,
  system_prompt, response_model)`, LangChain-based. Builds three
  `.with_structured_output(response_model)`-wrapped chat models (Gemini, Mistral,
  OpenAI) and chains them with `.with_fallbacks()` — Gemini first, Mistral and OpenAI
  as fallbacks in that order — then calls `.ainvoke()` once. `response_model` is
  applied to *all three* before chaining, not just the primary, so a mid-chain
  fallback still returns the same structured shape the caller expects.
- **`models.py`** — every data shape that isn't a database table (that's
  `common/models.py` instead): Pydantic contracts the LLM must produce
  (`Mistake`/`Mistakes` from gap analysis, `RecommendedExercise`/`RecommendedExercises`
  from the second LLM pass) and plain internal dataclasses used to pass already-built
  data between this project's own functions (`MistakeWithExercises` — one gap plus its
  retrieved candidate exercises; `FinalRecommendation` — one gap's final description,
  best exercise, and the rest of the candidates, what the template renders). Keeping
  these three kinds of structure (DB rows, LLM contracts, internal DTOs) distinct
  matters: putting ORM objects straight into an LLM-facing Pydantic model, for
  instance, means the LLM's own schema ends up describing a field only this project's
  code is supposed to fill in.
- **`retrieval.py`** — `get_exercises(mistakes)`: for each identified gap, embeds its
  `topic` (`gemini-embedding-2-preview`, 768 dims — must match the dimension used when
  the textbook was indexed) and runs two independent `pgvector` similarity searches
  against `common.models.Exercise` — one by `embedded_summary`, one by
  `embedded_sub_topic` — combined via weighted Reciprocal Rank Fusion
  (`reciprocal_rank_fusion`, sub-topic weighted higher — it's the more reliable
  grouping signal). A short topic label and a specific, distinguishing exercise
  summary cluster differently in embedding space; searching `summary` alone, in
  practice, missed exercises on the exact same grammar point that just happened to be
  worded around different example content — the two-field fusion recovers those.
- **`analysis.py`** — `process_analysis` is a two-LLM-call pipeline, not one: gap
  analysis (`make_request_to_LLM` → `Mistakes`) → retrieval (`get_exercises`, returns
  `[]` early if no gaps were found — no second LLM call to recommend exercises for
  nothing) → a second `make_request_to_LLM` call that picks the best-matching
  candidate per gap (`RecommendedExercises`) → `build_final_recommendations` resolves
  each recommendation's `best_exercise_id`/`other_exercise_ids` back to the actual
  `Exercise` rows already fetched in the retrieval step (no second database query —
  the candidates are already in memory) and reattaches the original gap's
  `description` (looked up by `index`, a position the LLM is asked to echo back
  rather than re-type the gap's text, which it isn't asked to reproduce verbatim).
  `analyse_student`/`analyse_class` differ only in which `format_*` function and which
  prompt they feed into this same pipeline.
- **`settings.py`** — loads `.env` once and validates every required var is present at
  import time (raises immediately, not deep inside some later HTTP call).
  `OPENAI_API_KEY` is deliberately not one of them — nothing here reads it directly,
  `langchain-openai`'s `ChatOpenAI` picks it up from the environment on its own.

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
- `make_request_to_LLM` tests patch the three LangChain chat classes where they're
  *imported* (`app.providers.ChatGoogleGenerativeAI`, not
  `langchain_google_genai.ChatGoogleGenerativeAI`) — same reason as always, `from x
  import Y` binds a separate name in the importing module. All three must be patched
  even when the test only cares about the Gemini path: `make_request_to_LLM`
  constructs all three unconditionally before chaining `.with_fallbacks()`, and
  `.env.test` has no `OPENAI_API_KEY`, so an unpatched `ChatOpenAI` would fail to
  construct. Because each is a `MagicMock`, asserting on the chain (e.g.
  `gemini.with_fallbacks.assert_called_once_with([mistral, openai])`) only verifies
  *this project's* wiring, not LangChain's own fallback behavior — that's the
  library's responsibility to get right, not something to re-test here.
- `process_analysis` tests (`test_analysis.py`) patch `make_request_to_LLM` with a
  `side_effect` list of two different return values — it's called twice per
  request (gap analysis, then exercise recommendation) with two different
  `response_model`s — plus `get_exercises`, so no real embedding/database calls
  happen in a unit test.
- Decorator stacking order is easy to get backwards: stacked `@patch` decorators are
  applied bottom-up, so the mock for the decorator *closest to the function* becomes
  the *first* parameter, not the last.

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
