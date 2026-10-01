# SmartRecall — Project Context (paste this into every Claude chat before your task prompt)

You are helping build **SmartRecall**, a Flask + SQLite + Gemini API flashcard/quiz study app, for a university software engineering course. Three teammates are working in parallel using separate Claude chats, so **you must follow this spec exactly** so our code fits together without conflicts. Do not deviate from file names, function names, or folder structure below, even if you'd normally do it differently.

## What the app does

A user pastes raw study text (notes, textbook excerpt) into a form. The app sends that text to the Gemini API, which returns a set of flashcards (question/answer pairs). The flashcards are saved to a SQLite database under a "deck," and the user can view them on a results page.

## Tech stack (do not substitute or add anything)

- **Backend:** Python, Flask (monolithic single app, no microservices)
- **Database:** SQLite (file-based), accessed only through the model functions listed below — no raw SQL in routes
- **AI:** Google Gemini API, called only from `backend/services/ai_service.py` — no other file should call Gemini directly
- **Frontend:** Jinja2 server-rendered templates + plain vanilla JavaScript (no React/Vue, no build step, no npm frontend tooling)
- **Testing:** `pytest`, `pytest-cov`, `pytest-mock`

## Folder structure (exact — create only files relevant to your task, don't restructure)

```
smartrecall/
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── deck.html
│   │   ├── study_flip.html
│   │   ├── study_quiz.html
│   │   └── dashboard.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── flashcards.py
│   │   ├── decks.py
│   │   └── dashboard.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   └── spaced_repetition.py
│   └── models/
│       ├── __init__.py
│       ├── deck.py
│       └── card.py
├── database/
│   ├── schema.sql
│   └── seed_data.sql
├── testing/
│   ├── test_ai_service.py
│   ├── test_models.py
│   └── test_routes.py
├── .env.example
├── .gitignore
└── CLAUDE.md
```

## Layered architecture rule (follow strictly)

**Routes → Services → Models → Database.** A route must never call the database or the Gemini API directly. A route calls a service function; a service function calls a model function if it needs the database.

## Required function signatures (use these exact names and arguments)

### `backend/models/deck.py`
```python
def create_deck(name: str) -> int:
    """Creates a new deck, returns its id."""

def get_deck(deck_id: int) -> dict:
    """Returns {id, name} for a deck, or None if not found."""
```

### `backend/models/card.py`
```python
def save_cards(deck_id: int, cards: list[dict]) -> None:
    """Saves a list of {question, answer} dicts to the given deck."""

def get_cards(deck_id: int) -> list[dict]:
    """Returns all cards for a deck as a list of dicts."""
```

### `backend/services/ai_service.py`
```python
def generate_flashcards(text: str) -> list[dict]:
    """
    Calls the Gemini API with the given text, asks for flashcard JSON output,
    parses and returns a list of {question, answer} dicts.
    Must raise a clear exception (not crash silently) if the API call fails
    or the response isn't valid JSON.
    """
```

### `backend/routes/flashcards.py`
```python
# Route: GET /  -> renders frontend/templates/index.html (the paste-text form)
# Route: POST /generate -> reads form text, calls ai_service.generate_flashcards(),
#        calls deck.create_deck() and card.save_cards(), then renders deck.html
```

## Database schema (`database/schema.sql`)

```sql
CREATE TABLE decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    difficulty TEXT DEFAULT 'medium',
    next_review_date TIMESTAMP,
    FOREIGN KEY (deck_id) REFERENCES decks(id)
);
```

## Coding conventions

- Python: use type hints on every function, follow PEP 8, docstrings on every public function.
- No hardcoded secrets anywhere — Gemini API key and Flask secret key come from environment variables via `.env` (see `.env.example`).
- Every function that touches the database or the Gemini API must handle and raise clear errors — no silent failures.
- Keep functions short and single-purpose; don't combine "generate + save + render" into one giant function — split across the route/service/model layers as shown above.
- Variable and function names: `snake_case`. File names: `snake_case.py`.

## Testing requirements

- Tests live in `testing/`, named `test_<module>.py`, using `pytest`.
- Mock the Gemini API in tests — never call the real API from a test (use `pytest-mock` or `unittest.mock.patch`).
- Use a temporary or in-memory SQLite database for model tests — never touch the real `database/smartrecall.db` in tests.
- Target: at least 80% line coverage on the feature you're assigned, checked with:
  ```
  pytest --cov=backend --cov-report=term-missing
  ```

## Team and task assignment (for your reference — only build what's listed as yours)

| Person | Files they own |
|---|---|
| Alex | `database/schema.sql`, `backend/models/deck.py`, `backend/models/card.py`, `testing/test_models.py` |
| Yasir | `backend/services/ai_service.py`, `backend/routes/flashcards.py`, `backend/app.py`, `testing/test_ai_service.py` |
| Moustapha | `frontend/templates/index.html`, `frontend/templates/deck.html`, `backend/requirements.txt`, `testing/test_routes.py` |

## Your task

After pasting this file into the chat, follow it with one line stating exactly which file(s) from the table above you are building right now, and ask Claude to write only that file, following every rule above exactly.
