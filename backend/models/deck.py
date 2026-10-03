"""Deck model: all database access for the ``decks`` table."""

import os
import sqlite3
from pathlib import Path
from typing import Optional

_DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[2] / "database" / "smartrecall.db"
)


def _get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with row access by column name.

    The database path comes from the DATABASE_PATH environment variable
    if set (used by tests), otherwise database/smartrecall.db.

    Raises:
        RuntimeError: If the database cannot be opened.
    """
    db_path = os.environ.get("DATABASE_PATH", str(_DEFAULT_DB_PATH))
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not open database at {db_path}: {exc}") from exc
    return conn


def create_deck(name: str) -> int:
    """Create a new deck and return its id.

    Raises:
        ValueError: If name is not a non-empty string.
        RuntimeError: If the database operation fails.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Deck name must be a non-empty string.")

    conn = _get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO decks (name) VALUES (?)", (name.strip(),)
            )
            return int(cursor.lastrowid)
    except sqlite3.Error as exc:
        raise RuntimeError(f"Failed to create deck: {exc}") from exc
    finally:
        conn.close()


def get_deck(deck_id: int) -> Optional[dict]:
    """Return {id, name} for a deck, or None if not found.

    Raises:
        ValueError: If deck_id is not an integer.
        RuntimeError: If the database operation fails.
    """
    if not isinstance(deck_id, int) or isinstance(deck_id, bool):
        raise ValueError("deck_id must be an integer.")

    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT id, name FROM decks WHERE id = ?", (deck_id,)
        ).fetchone()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Failed to fetch deck {deck_id}: {exc}") from exc
    finally:
        conn.close()

    return dict(row) if row is not None else None
