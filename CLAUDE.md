# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python service that analyzes student answers from EduCore (a Rails app) — **all answer
types**, not just `long_text`; a wrong `multiple_choice` option or a wrong `short_text`
answer carries the same kind of signal as a `long_text` mistake — to detect learning
gaps (grammar, vocabulary, verb tense, etc.) and generate teacher-facing
recommendations, per student and per class. See `README.md` for the one-paragraph pitch.

**Status: skeleton only.** Poetry + FastAPI (`main.py`/`routes.py`) with dependencies
chosen (`google-genai`, `mistralai`, `httpx`) but no real routes or `educore`-consuming
logic yet beyond a placeholder `/`. Update this file's structure/architecture as real
code lands, following the same style as `../educore/CLAUDE.md` (commands + big-picture
architecture, not a file listing).

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
  (`in_progress`/`evaluating`/`completed`), `score`, `grade`
- `Student`/`SchoolClass` — for grouping detected error patterns per student and per class

**Data access: via API, built.** `GET /api/test_attempts`, token auth
(`Authorization: Bearer <token>` — the same secret value must be set in both
projects' env; `educore` calls it `ANALYTICS_API_KEY`, this project stores it as
`EDUCORE_API_KEY` in `.env`/`settings.py`), filterable by
`test_id`/`student_id`/`school_class_id`/`subject`.
Full contract, including the exact response shape and known gaps (no pagination, no
versioning yet):

@../educore/docs/API_CONTRACT.md
