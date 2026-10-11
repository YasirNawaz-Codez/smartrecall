# SmartRecall

SmartRecall is an AI-powered flashcard study tool. Paste in your notes, and it uses the Google Gemini API to generate a set of question and answer flashcards, saves them to a database, and shows them on a results page.

Built for CSCI 4397/6397 (Software Engineering and AI) at the University of Central Arkansas, Fall 2026.

**Team:** Yasir Nawaz, Moustapha Fofana, Alex Du

See [AI_USAGE.md](AI_USAGE.md) for how our team used AI tools to build this project.

## Features

**Implemented**

- Paste any text (notes, textbook excerpts) and get AI-generated flashcards
- Flashcards are saved to a SQLite database, grouped into a deck
- Deck page that displays every generated question and answer
- Clear error messages when the AI call or database fails
- Automatic database setup on first run (no manual steps)

**Planned**

- Multiple study modes: multiple choice, true/false, fill-in-the-blank
- Simplified spaced repetition (rate cards Easy, Medium, Hard)
- Progress dashboard (cards studied, accuracy, study streak)
- AI-graded short answers

## Tech Stack

- Backend: Python, Flask
- Database: SQLite
- AI: Google Gemini API (`google-genai` SDK, model `gemini-3.8-flash`)
- Frontend: Jinja2 templates, HTML, CSS, JavaScript
- Testing: pytest, pytest-cov, pytest-mock

## Getting Started

These steps assume you only have the GitHub link and a fresh computer.

### 1. Install the prerequisites

- **Python 3.10 or newer.** Download from https://www.python.org/downloads/. On Windows, check the box **"Add python.exe to PATH"** on the first installer screen. Confirm it worked:
  ```
  python --version
  ```
- **Git** (https://git-scm.com/downloads) or **GitHub Desktop** (https://desktop.github.com/).
- A **free Google Gemini API key** (see step 4).

If the repository is private, ask a team member to invite your GitHub account as a collaborator before you try to clone it.

### 2. Clone the repository

```
git clone https://github.com/YasirNawaz-Codez/smartrecall.git
cd smartrecall
```

(With GitHub Desktop: File, Clone repository, paste the URL, then open the folder in a terminal.)

All commands below are run from this project root folder, the one that contains `backend/`, `frontend/`, and `database/`.

### 3. Create a virtual environment and install dependencies

A virtual environment keeps this project's packages separate from the rest of your computer.

**Windows (Command Prompt or PowerShell):**
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r backend/requirements.txt
```

**macOS / Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r backend/requirements.txt
```

When the environment is active you will see `(.venv)` at the start of your terminal line.

### 4. Get a Gemini API key and add it to `.env`

1. Go to https://aistudio.google.com/apikey and sign in with any Google account.
2. Click **Create API key** and copy it. The free tier is enough for this project and needs no credit card.
3. In the project root, copy the example file to a new file named `.env`:

   **Windows:**
   ```
   copy .env.example .env
   ```
   **macOS / Linux:**
   ```
   cp .env.example .env
   ```
4. Open `.env` in any text editor and replace the placeholder with your real key:
   ```
   GEMINI_API_KEY=your_real_key_here
   FLASK_SECRET_KEY=any_random_string
   ```
   Do not add quotes or spaces around the values. The `.env` file is listed in `.gitignore`, so it will never be committed. **Never commit or share your API key.**

### 5. Run the app

```
python -m backend.app
```

Then open **http://127.0.0.1:5000** in your browser.

There is no database setup step. On first launch the app creates `database/smartrecall.db` and its tables automatically from `database/schema.sql`.

### 6. Try it

1. Paste a few paragraphs of notes into the text box.
2. Click **Generate**.
3. Wait a few seconds. You should land on a deck page listing the generated flashcards.

To stop the server, press `Ctrl+C` in the terminal.

## Running the Tests

With the virtual environment active, from the project root:

```
python -m pytest --cov=backend --cov-report=term-missing
```

The tests do **not** need an API key or an internet connection. The Gemini API is mocked in every test, and each test uses a temporary database, so your real data is never touched.

The coverage table in the output shows, per file, which lines ran during the tests and which line numbers did not.

## Project Structure

```
smartrecall/
├── backend/
│   ├── app.py              Flask app factory and database setup
│   ├── routes/             HTTP routes (flashcards.py handles / and /generate)
│   ├── services/           Business logic (ai_service.py is the only file that calls Gemini)
│   ├── models/             Database access (deck.py, card.py)
│   └── requirements.txt
├── frontend/
│   ├── templates/          Jinja2 HTML pages (index.html, deck.html)
│   └── static/             CSS and JavaScript
├── database/
│   └── schema.sql          Table definitions (smartrecall.db is created at runtime)
├── testing/                pytest test suites
├── docs/                   Architecture documentation
├── AI_USAGE.md             How we used AI tools
├── CLAUDE.md               Project rules for AI coding assistants
└── .env.example            Template for your local .env file
```

The code follows a strict layering rule: routes call services, services call models, and models talk to the database. Routes never call the database or the Gemini API directly. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design.

## Troubleshooting

| Problem | Fix |
|---|---|
| `pip` or `pytest` is "not recognized" | Always run them through Python: `python -m pip ...` and `python -m pytest ...`. If `python` itself is not recognized, reinstall Python and check "Add python.exe to PATH". |
| `ModuleNotFoundError` when starting | Run the app from the project root with `python -m backend.app`, not from inside `backend/`. Also make sure the virtual environment is active. |
| Error box says `GEMINI_API_KEY is not set` | The `.env` file is missing, misnamed (it must be exactly `.env`), or not in the project root. |
| Error box shows `503 UNAVAILABLE` | Google's servers are busy. Wait a minute and click Generate again. |
| Error box shows `404 NOT_FOUND` for the model | Google retired the model name. Update `_MODEL_NAME` in `backend/services/ai_service.py` to the replacement named in the error message. |
| Error box shows `API key not valid` | Re-copy the key from https://aistudio.google.com/apikey and check for stray spaces in `.env`. |
| Port 5000 already in use | Stop the other program using it, or change the port in the last line of `backend/app.py`. |

## License and Course Use

This is a student project for academic use.
