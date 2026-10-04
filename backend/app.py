"""SmartRecall Flask application entry point."""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_FOLDER = _PROJECT_ROOT / "frontend" / "templates"
_STATIC_FOLDER = _PROJECT_ROOT / "frontend" / "static"
_DB_PATH = _PROJECT_ROOT / "database" / "smartrecall.db"
_SCHEMA_PATH = _PROJECT_ROOT / "database" / "schema.sql"


def init_db() -> None:
    """Create the database tables if they don't already exist.

    Safe to call every time the app starts. Checks for the 'decks'
    table first so it never re-runs CREATE TABLE against a database
    that's already set up (which would crash, since schema.sql doesn't
    use IF NOT EXISTS). On a fresh clone with no database file yet,
    this creates it from schema.sql automatically.
    """
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(_DB_PATH)
    try:
        existing_tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='decks'"
        ).fetchall()
        if not existing_tables:
            with open(_SCHEMA_PATH, "r") as f:
                conn.executescript(f.read())
            conn.commit()
    finally:
        conn.close()


def create_app() -> Flask:
    """Application factory: builds and configures the Flask app."""
    app = Flask(
        __name__,
        template_folder=str(_TEMPLATE_FOLDER),
        static_folder=str(_STATIC_FOLDER),
    )
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")

    init_db()

    from backend.routes.flashcards import flashcards_bp
    app.register_blueprint(flashcards_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
