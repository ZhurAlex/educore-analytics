# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python service that analyzes student answers from EduCore (a Rails app) — **all answer
types**, not just `long_text`; a wrong `multiple_choice` option or a wrong `short_text`
answer carries the same kind of signal as a `long_text` mistake — to detect learning
gaps (grammar, vocabulary, verb tense, etc.) and generate teacher-facing
recommendations, per student and per class. See `README.md` for the one-paragraph pitch.

**Status: MVP working end-to-end.** FastAPI service, stateless — no database; every
request re-reads from `educore`'s API, nothing persisted here. Two analysis endpoints
call an LLM (Gemini, falling back to Mistral) and return a plain-text recommendation.

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
```

## Architecture

All application modules live under `app/` (a plain package — `python -m app.main` or
`uvicorn app.main:app`, not `python app/main.py`, which runs outside the package and
breaks the absolute imports below). Tests, once added, live in a separate top-level
`tests/`, mirroring this layout.

### Request flow

`app/routes.py` exposes three endpoints:
- `GET /get_test_attempts` — thin passthrough to `educore`'s API, raw JSON. Debug/plumbing
  endpoint, not the product — kept from before the analysis endpoints existed.
- `GET /students/{student_id}/gap-analysis` — one student's history for one subject,
  analyzed for recurring mistakes and *forgetting* (a topic answered correctly in one
  attempt, wrong again in a later one).
- `GET /class/{test_id}/class-analysis` — one test, whole class: which questions/topics
  the class struggled with most, aggregated in code before ever reaching the LLM.

Both analysis endpoints return `PlainTextResponse`, not JSON — the payload is a
markdown recommendation meant for a teacher to read, not structured data for a program
to parse further.

### Module boundaries

- **`educore_client.py`** — the only place that speaks HTTP to `educore`'s
  `/api/test_attempts`. Deliberately has no FastAPI import — raises plain `httpx`
  exceptions rather than `HTTPException`, so it isn't tied to this web framework and
  could be reused outside it. `routes.py` is where those exceptions get translated
  into HTTP responses.
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

**Data access: via API, built.** `GET /api/test_attempts`, token auth
(`Authorization: Bearer <token>` — the same secret value must be set in both
projects' env; `educore` calls it `ANALYTICS_API_KEY`, this project stores it as
`EDUCORE_API_KEY` in `.env`/`settings.py`), filterable by
`test_id`/`student_id`/`school_class_id`/`subject`.
Full contract, including the exact response shape and known gaps (no pagination, no
versioning yet):

@../educore/docs/API_CONTRACT.md
