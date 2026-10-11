# AI Usage in SmartRecall

CSCI 4397 / CSCI 6397: Software Engineering and AI, Fall 2026, University of Central Arkansas
Team: Yasir Nawaz, Moustapha Fofana, Alex Du

This document describes how our team used AI tools to build SmartRecall, how we kept those tools consistent across three people, and how we checked their output before trusting it.

## 1. AI tools used

| Tool | Where it was used | Who used it |
|---|---|---|
| Claude (chat) | Planning, drafting code, debugging, writing PR descriptions and documentation | Yasir, Alex |
| Claude Code | Drafting and iterating on test code | Moustapha |
| Google Gemini API (`gemini-3.8-flash`) | Inside the app itself: turns pasted notes into flashcards at runtime | The app (called only from `backend/services/ai_service.py`) |

There are two different kinds of AI use in this project, and it is worth keeping them apart:

1. **AI as a development tool.** Claude helped us write and debug the code.
2. **AI as an application component.** Gemini is part of the running product. Its output is treated as untrusted input and validated before it reaches the database or the UI.

## 2. Shared standards across separate AI sessions

Each teammate worked in a separate AI chat, so without a shared spec the three sets of generated code would not have fit together. We handled this two ways:

- **`CLAUDE.md`** in the repo root describes the stack, the layering rule (routes call services, services call models, models call the database), and the coding conventions.
- **A project context brief** (the full spec: folder structure, exact function signatures, database schema, coding conventions, and file ownership) was pasted at the start of every teammate's AI session before any task prompt. This is what made code from three independent sessions integrate. For example, Moustapha's form field name `text` and the `deck.name` / `cards` variables in his templates matched the route Yasir wrote, and Alex's `create_deck`, `get_deck`, `save_cards`, and `get_cards` signatures matched what the route calls.

## 3. Who used AI for what

| Person | Files | How AI was used |
|---|---|---|
| Yasir | `backend/services/ai_service.py`, `backend/routes/flashcards.py`, `backend/app.py`, `testing/test_ai_service.py` | Claude drafted the code from the shared spec. Yasir ran it, debugged failures against real error output, and corrected it (see section 5). |
| Alex | `database/schema.sql`, `backend/models/deck.py`, `backend/models/card.py`, `testing/test_models.py` | Claude helped draft the models and the model test suite (65 tests). Alex listed every branch in the models, wrote tests to reach each one, and checked results against the real code. |
| Moustapha | `frontend/templates/index.html`, `frontend/templates/deck.html`, `testing/test_routes.py`, `pytest.ini` | Claude Code helped write the templates and the route integration tests. Moustapha reviewed each test before committing. |

## 4. How we verified AI output

We did not treat generated code as correct because it looked plausible. Our checks were:

- **Human review on every PR.** Every pull request was approved by a teammate other than its author before merging.
- **Running the code.** Each person ran their files locally against real inputs, not just the tests.
- **Mocked tests.** The Gemini API is mocked in every test, so tests are repeatable, cost nothing, and need no API key. Model and route tests use a temporary SQLite database, and a guard in the model tests fails if any test touches the real `database/smartrecall.db`.
- **Coverage measurement.** Combined backend coverage is above the 80 percent requirement (84 to 86 percent for the full backend, 100 percent for the models alone). Coverage only shows which lines ran, so the tests also assert on returned values and error messages.
- **Validating the Gemini output.** `ai_service.py` checks that the response is valid JSON in the expected shape, with non-empty `question` and `answer` strings, and raises a clear error otherwise. Malformed AI output never reaches the database.
- **Secrets.** The API key lives only in a local `.env` file, which is gitignored. `.env.example` shows the format.

## 5. AI audit log: where AI output was wrong or needed correction

These are real problems we hit and fixed. They are the main evidence that AI output was checked rather than copied.

| # | What the AI produced | What went wrong | How we caught it | Fix |
|---|---|---|---|---|
| 1 | `ai_service.py` first used the `google-generativeai` package | That package is deprecated | pytest printed a deprecation warning | Switched to the current `google-genai` SDK and updated the tests and `requirements.txt` |
| 2 | Model name `gemini-2.0-flash` | Google retired the model; the live API returned a 404 | The app showed the error message when we ran it for real | Updated to `gemini-3.8-flash`, which the error message named |
| 3 | The Generate button appeared to do nothing when something failed | The route caught the error and re-rendered the form, but the template had no place to show it | Debugging a "silent refresh" | Added a visible error box to `index.html` |
| 4 | Database startup | Nothing created the tables, so a fresh clone failed with `no such table: decks` | Moustapha's route tests exposed it | Added `init_db()` in `app.py` to create tables on startup |
| 5 | First draft of `init_db()` re-ran `CREATE TABLE` on every start | It would crash on the second launch, because `schema.sql` has no `IF NOT EXISTS` | Tested a simulated restart before shipping | Check whether the `decks` table exists first, and only then run the schema |
| 6 | `init_db()` used a hardcoded database path | Ignored `DATABASE_PATH`, and `app = create_app()` ran at import time, so the test suite quietly created a real `smartrecall.db` | Reviewer feedback from a teammate | Read `DATABASE_PATH` like the models do, and build the app only under `if __name__ == "__main__"` |
| 7 | A stash/merge during a branch switch | Left unresolved conflict markers in `app.py`, a syntax error that broke test collection on `main` | Alex noticed when `test_routes.py` failed to collect | Restored the correct file, verified it parses and the suite passes |

Lessons we took from this: AI-generated code needs to be run, not just read; deprecated or retired APIs are a common AI failure; and a high coverage number on one file can hide a low number for the whole feature (a single-file 95 percent coverage figure turned out to be 24 percent across the backend until route tests were added).

## 6. Rules the team follows

- No AI-generated code is merged without a review by a different teammate.
- AI output used at runtime (Gemini responses) is validated before use.
- Secrets are never committed.
- Tests never call the real Gemini API and never touch the real database.
- Anything an AI tool contributes to a PR is disclosed in that PR's description.

## 7. Known limitations

- The only AI feature implemented so far is flashcard generation. Quiz modes, spaced repetition, and AI-graded answers from the proposal are not built yet.
- Gemini's free tier sometimes returns `503 UNAVAILABLE` during high demand. The app shows the error and the user retries; automatic retry is not implemented.
- Generated flashcards are not fact-checked by the app. A student should still verify them against their source notes.
