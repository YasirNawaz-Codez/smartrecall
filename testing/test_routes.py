"""Tests for backend/routes/flashcards.py. Every test runs against a
temporary SQLite database in tmp_path, and generate_flashcards() is mocked
so the real Gemini API is never called and no API key is needed."""

import sqlite3
from pathlib import Path

import pytest

from backend.app import create_app
from backend.services import ai_service

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _PROJECT_ROOT / "database" / "schema.sql"
_REAL_DB_PATH = _PROJECT_ROOT / "database" / "smartrecall.db"

_REAL_GENERATE_FLASHCARDS = ai_service.generate_flashcards


def _real_db_state():
    """Return (exists, mtime) for the real database file."""
    if not _REAL_DB_PATH.exists():
        return (False, None)
    return (True, _REAL_DB_PATH.stat().st_mtime_ns)


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point the models at a fresh temporary database with the real schema."""
    real_db_before = _real_db_state()

    path = tmp_path / "test.db"
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA_PATH.read_text())
    conn.close()
    monkeypatch.setenv("DATABASE_PATH", str(path))

    yield path

    assert _real_db_state() == real_db_before, "Test touched the real database file"


@pytest.fixture
def client(db_path, monkeypatch):
    """Flask test client with no Gemini API key available."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def mock_generate(mocker):
    """Replace generate_flashcards with a mock; tests set its behaviour."""
    return mocker.patch("backend.services.ai_service.generate_flashcards")


def _count_rows(db_path, table):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def test_index_shows_form(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<form action="/generate" method="post">' in html
    assert 'name="text"' in html
    assert "Something went wrong" not in html


def test_generate_shows_cards_on_deck_page(client, db_path, mock_generate):
    mock_generate.return_value = [
        {"question": "What do plants convert light into?", "answer": "Chemical energy"},
        {"question": "Where does photosynthesis happen?", "answer": "In the chloroplasts"},
    ]
    text = "Photosynthesis converts light energy into chemical energy in plants."

    response = client.post("/generate", data={"text": text})

    assert response.status_code == 200
    mock_generate.assert_called_once_with(text)
    html = response.get_data(as_text=True)
    assert "<h1>Photosynthesis converts light energy into chemical...</h1>" in html
    assert "2 cards" in html
    assert "Q: What do plants convert light into?" in html
    assert "A: Chemical energy" in html
    assert "Q: Where does photosynthesis happen?" in html
    assert "A: In the chloroplasts" in html
    assert _count_rows(db_path, "decks") == 1
    assert _count_rows(db_path, "cards") == 2


@pytest.mark.parametrize("text", ["", "   \n  "])
def test_generate_with_empty_text_shows_error(client, db_path, mocker, text):
    # Wrap the real function so its own empty-text check runs; it raises
    # before creating a Gemini client, and no API key is set anyway.
    spy = mocker.patch(
        "backend.services.ai_service.generate_flashcards",
        wraps=_REAL_GENERATE_FLASHCARDS,
    )

    response = client.post("/generate", data={"text": text})

    assert response.status_code == 400
    spy.assert_called_once_with(text)
    html = response.get_data(as_text=True)
    assert "Something went wrong:" in html
    assert "text must be a non-empty string." in html
    assert '<form action="/generate" method="post">' in html
    assert _count_rows(db_path, "decks") == 0
    assert _count_rows(db_path, "cards") == 0


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("Gemini API call failed: network down"),
        ValueError("Gemini did not return valid JSON"),
    ],
)
def test_generate_when_ai_service_fails_shows_error(client, db_path, mock_generate, error):
    mock_generate.side_effect = error

    response = client.post("/generate", data={"text": "Some study notes."})

    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "Something went wrong:" in html
    assert str(error) in html
    assert '<form action="/generate" method="post">' in html
    assert _count_rows(db_path, "decks") == 0
    assert _count_rows(db_path, "cards") == 0
