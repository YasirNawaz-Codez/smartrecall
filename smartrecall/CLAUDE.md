# SmartRecall

Flask + SQLite + Gemini API flashcard/quiz study app.

## Stack
- Backend: Python (Flask), organized as routes -> services -> models
- Database: SQLite (database/smartrecall.db)
- AI: Google Gemini API, called only from backend/services/ai_service.py
- Frontend: Jinja2 templates + vanilla JS, served by the same Flask process from frontend/

## Conventions
- Routes never call the database or Gemini API directly; always go through services/models.
- All secrets in .env, never committed.
- Every PR reviewed by at least one teammate before merging to main.
