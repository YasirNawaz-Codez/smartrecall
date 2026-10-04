"""SmartRecall Flask application entry point."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_FOLDER = _PROJECT_ROOT / "frontend" / "templates"
_STATIC_FOLDER = _PROJECT_ROOT / "frontend" / "static"


def create_app() -> Flask:
    """Application factory: builds and configures the Flask app."""
    app = Flask(
        __name__,
        template_folder=str(_TEMPLATE_FOLDER),
        static_folder=str(_STATIC_FOLDER),
    )
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")

    from backend.routes.flashcards import flashcards_bp
    app.register_blueprint(flashcards_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
