"""Card model: all database access for the ``cards`` table."""

import os
import sqlite3
from pathlib import Path

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


def _validate_cards(cards: list[dict]) -> list[tuple[str, str]]:
    """Check every card has a non-empty question and answer.

    Returns:
        A list of (question, answer) tuples ready for insertion.

    Raises:
        ValueError: If cards is empty or any card is malformed.
    """
    if not isinstance(cards, list) or not cards:
        raise ValueError("cards must be a non-empty list of dicts.")

    rows: list[tuple[str, str]] = []
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            raise ValueError(f"Card at index {index} is not a dict.")
        question = card.get("question")
        answer = card.get("answer")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Card at index {index} has no valid 'question'.")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError(f"Card at index {index} has no valid 'answer'.")
        rows.append((question.strip(), answer.strip()))
    return rows


def save_cards(deck_id: int, cards: list[dict]) -> None:
    """Save a list of {question, answer} dicts to the given deck.

    All cards are saved in a single transaction: either all succeed or
    none are stored.

    Raises:
        ValueError: If deck_id or cards are invalid.
        RuntimeError: If the deck does not exist or the database fails.
    """
    if not isinstance(deck_id, int) or isinstance(deck_id, bool):
        raise ValueError("deck_id must be an integer.")
    rows = _validate_cards(cards)

    conn = _get_connection()
    try:
        with conn:
            conn.executemany(
                "INSERT INTO cards (deck_id, question, answer) VALUES (?, ?, ?)",
                [(deck_id, question, answer) for question, answer in rows],
            )
    except sqlite3.IntegrityError as exc:
        raise RuntimeError(
            f"Could not save cards; deck {deck_id} may not exist: {exc}"
        ) from exc
    except sqlite3.Error as exc:
        raise RuntimeError(f"Failed to save cards: {exc}") from exc
    finally:
        conn.close()


def get_cards(deck_id: int) -> list[dict]:
    """Return all cards for a deck as a list of dicts (empty if none).

    Each dict has: id, deck_id, question, answer, difficulty,
    next_review_date.

    Raises:
        ValueError: If deck_id is not an integer.
        RuntimeError: If the database operation fails.
    """
    if not isinstance(deck_id, int) or isinstance(deck_id, bool):
        raise ValueError("deck_id must be an integer.")

    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT id, deck_id, question, answer, difficulty, next_review_date "
            "FROM cards WHERE deck_id = ? ORDER BY id",
            (deck_id,),
        ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(
            f"Failed to fetch cards for deck {deck_id}: {exc}"
        ) from exc
    finally:
        conn.close()

    return [dict(row) for row in rows]
