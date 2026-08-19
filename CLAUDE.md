# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python service that analyzes student answers from EduCore (a Rails app) — **all answer
types**, not just `long_text`; a wrong `multiple_choice` option or a wrong `short_text`
answer carries the same kind of signal as a `long_text` mistake — to detect learning
gaps (grammar, vocabulary, verb tense, etc.) and generate teacher-facing
recommendations, per student and per class. See `README.md` for the one-paragraph pitch.

**Status: not yet built.** This file exists to capture context about the companion
project before it's needed, not to describe code that exists here yet — update it once
real structure/conventions exist, following the same style as `../educore/CLAUDE.md`
(commands + big-picture architecture, not a file listing).

## Companion project: `../educore`

The Rails app this service reads from. Full schema/architecture:
`../educore/docs/SPEC.md` and `../educore/CLAUDE.md`.

Relevant pieces for this project specifically:

- `Question` — `answer_type` (`multiple_choice`/`short_text`/`long_text`),
  `correct_answer` (for `long_text`: a reference answer/rubric passed to Gemini, not a
  string it's compared against verbatim the way it is for `short_text`)
- `Response` — one per (attempt, question), for **every** answer type, not just
  `long_text`: `answer_text` (`short_text`/`long_text`) or `option_id`
  (`multiple_choice` — join to `Option#body`/`correct` to see what was picked vs. what
  was right), `points_awarded`, `feedback` (only ever populated for `long_text` —
  Gemini's explanation, or a teacher's own note; `nil` for the other two types),
  `grading_status` (`auto_graded`/`teacher_overridden`/`pending`/`llm_graded`/
  `manual_check_required` — the last one means Gemini grading failed and a teacher
  hasn't reviewed it yet, worth excluding or flagging separately in any analysis)
- `TestAttempt` — `student_id`, `test_id`, `status`
  (`in_progress`/`evaluating`/`completed`), `score`, `grade`
- `Student`/`SchoolClass` — for grouping detected error patterns per student and per class

**Data access: via an API, not direct database access (decided).** `educore` doesn't
expose one yet — that's a prerequisite piece of work on the `educore` side before this
project can pull real data, not something already available to build against. Once
that API exists, its contract should live in a small, dedicated file in `educore`
(not the full `docs/SPEC.md`, which covers the whole Rails app) — once that file
exists, `@`-import it here (e.g. `@../educore/docs/API_CONTRACT.md`) so it's pulled
into context automatically instead of needing a manual Read every session.
