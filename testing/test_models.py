"""Tests for backend/models/deck.py and backend/models/card.py.

Every test runs against a temporary SQLite database created in tmp_path from
the real database/schema.sql. The real database/smartrecall.db is never used.
"""

import sqlite3
from pathlib import Path

import pytest

from backend.models import card, deck

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _PROJECT_ROOT / "database" / "schema.sql"
_REAL_DB_PATH = _PROJECT_ROOT / "database" / "smartrecall.db"


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
def empty_db(tmp_path, monkeypatch):
    """Point the models at a valid SQLite file that has no tables."""
    path = tmp_path / "empty.db"
    sqlite3.connect(path).close()
    monkeypatch.setenv("DATABASE_PATH", str(path))
    return path


@pytest.fixture
def unopenable_db(tmp_path, monkeypatch):
    """Point the models at a path whose parent folder does not exist."""
    path = tmp_path / "missing_folder" / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    return path


def _sample_cards():
    return [
        {"question": "What is ATP?", "answer": "The cell's energy currency."},
        {"question": "What is DNA?", "answer": "Genetic material."},
    ]


# ---------------------------------------------------------------------------
# deck.create_deck
# ---------------------------------------------------------------------------


def test_create_deck_returns_integer_id(db_path):
    deck_id = deck.create_deck("Biology 101")

    assert isinstance(deck_id, int)
    assert deck_id == 1


def test_create_deck_ids_increment(db_path):
    first = deck.create_deck("First")
    second = deck.create_deck("Second")

    assert second == first + 1


def test_create_deck_strips_whitespace(db_path):
    deck_id = deck.create_deck("  Chemistry  ")

    assert deck.get_deck(deck_id) == {"id": deck_id, "name": "Chemistry"}


def test_create_deck_allows_duplicate_names(db_path):
    first = deck.create_deck("Same Name")
    second = deck.create_deck("Same Name")

    assert first != second


def test_create_deck_stores_special_characters(db_path):
    name = "Café 'quotes' \"double\"; DROP TABLE decks;--"
    deck_id = deck.create_deck(name)

    assert deck.get_deck(deck_id)["name"] == name
    # The decks table must still exist and be usable.
    assert deck.create_deck("Still works") > deck_id


@pytest.mark.parametrize("bad_name", ["", "   ", "\n\t", None, 123, ["x"]])
def test_create_deck_rejects_invalid_name(db_path, bad_name):
    with pytest.raises(ValueError, match="non-empty string"):
        deck.create_deck(bad_name)


def test_create_deck_invalid_name_saves_nothing(db_path):
    with pytest.raises(ValueError):
        deck.create_deck("   ")

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM decks").fetchone()[0]
    finally:
        conn.close()
    assert count == 0


def test_create_deck_raises_runtime_error_when_table_missing(empty_db):
    with pytest.raises(RuntimeError, match="Failed to create deck"):
        deck.create_deck("Biology")


def test_create_deck_raises_runtime_error_when_db_unopenable(unopenable_db):
    with pytest.raises(RuntimeError, match="Could not open database"):
        deck.create_deck("Biology")


# ---------------------------------------------------------------------------
# deck.get_deck
# ---------------------------------------------------------------------------


def test_get_deck_returns_id_and_name_only(db_path):
    deck_id = deck.create_deck("Biology 101")

    result = deck.get_deck(deck_id)

    assert result == {"id": deck_id, "name": "Biology 101"}
    assert set(result.keys()) == {"id", "name"}


def test_get_deck_returns_correct_deck_among_many(db_path):
    deck.create_deck("One")
    target = deck.create_deck("Two")
    deck.create_deck("Three")

    assert deck.get_deck(target)["name"] == "Two"


def test_get_deck_returns_none_when_not_found(db_path):
    assert deck.get_deck(9999) is None


@pytest.mark.parametrize("bad_id", ["1", None, 1.5, True, [1]])
def test_get_deck_rejects_non_integer_id(db_path, bad_id):
    with pytest.raises(ValueError, match="integer"):
        deck.get_deck(bad_id)


def test_get_deck_raises_runtime_error_when_table_missing(empty_db):
    with pytest.raises(RuntimeError, match="Failed to fetch deck"):
        deck.get_deck(1)


def test_get_deck_raises_runtime_error_when_db_unopenable(unopenable_db):
    with pytest.raises(RuntimeError, match="Could not open database"):
        deck.get_deck(1)


# ---------------------------------------------------------------------------
# card.save_cards
# ---------------------------------------------------------------------------


def test_save_cards_stores_all_cards(db_path):
    deck_id = deck.create_deck("Biology")

    result = card.save_cards(deck_id, _sample_cards())

    assert result is None
    assert len(card.get_cards(deck_id)) == 2


def test_save_cards_strips_whitespace(db_path):
    deck_id = deck.create_deck("Biology")

    card.save_cards(deck_id, [{"question": "  Q?  ", "answer": "\tA.\n"}])

    saved = card.get_cards(deck_id)[0]
    assert saved["question"] == "Q?"
    assert saved["answer"] == "A."


def test_save_cards_ignores_extra_keys(db_path):
    deck_id = deck.create_deck("Biology")

    card.save_cards(
        deck_id, [{"question": "Q", "answer": "A", "difficulty": "hard", "x": 1}]
    )

    saved = card.get_cards(deck_id)[0]
    assert saved["difficulty"] == "medium"


def test_save_cards_stores_special_characters(db_path):
    deck_id = deck.create_deck("Languages")
    question = "¿Qué significa 'hola'? \"Hello\"; DROP TABLE cards;--"
    answer = "こんにちは / مرحبا"

    card.save_cards(deck_id, [{"question": question, "answer": answer}])

    saved = card.get_cards(deck_id)[0]
    assert saved["question"] == question
    assert saved["answer"] == answer


def test_save_cards_handles_large_batch(db_path):
    deck_id = deck.create_deck("Big")
    cards = [{"question": f"Q{i}", "answer": f"A{i}"} for i in range(500)]

    card.save_cards(deck_id, cards)

    assert len(card.get_cards(deck_id)) == 500


def test_save_cards_appends_to_existing_cards(db_path):
    deck_id = deck.create_deck("Biology")

    card.save_cards(deck_id, [{"question": "Q1", "answer": "A1"}])
    card.save_cards(deck_id, [{"question": "Q2", "answer": "A2"}])

    assert [c["question"] for c in card.get_cards(deck_id)] == ["Q1", "Q2"]


@pytest.mark.parametrize("bad_cards", [[], None, "not a list", {"question": "Q"}])
def test_save_cards_rejects_empty_or_non_list(db_path, bad_cards):
    deck_id = deck.create_deck("Biology")

    with pytest.raises(ValueError, match="non-empty list"):
        card.save_cards(deck_id, bad_cards)


def test_save_cards_rejects_non_dict_card(db_path):
    deck_id = deck.create_deck("Biology")

    with pytest.raises(ValueError, match="index 1 is not a dict"):
        card.save_cards(deck_id, [{"question": "Q", "answer": "A"}, "oops"])


@pytest.mark.parametrize(
    "bad_card",
    [
        {"answer": "A"},
        {"question": "", "answer": "A"},
        {"question": "   ", "answer": "A"},
        {"question": None, "answer": "A"},
        {"question": 5, "answer": "A"},
    ],
)
def test_save_cards_rejects_invalid_question(db_path, bad_card):
    deck_id = deck.create_deck("Biology")

    with pytest.raises(ValueError, match="no valid 'question'"):
        card.save_cards(deck_id, [bad_card])


@pytest.mark.parametrize(
    "bad_card",
    [
        {"question": "Q"},
        {"question": "Q", "answer": ""},
        {"question": "Q", "answer": "   "},
        {"question": "Q", "answer": None},
        {"question": "Q", "answer": 5},
    ],
)
def test_save_cards_rejects_invalid_answer(db_path, bad_card):
    deck_id = deck.create_deck("Biology")

    with pytest.raises(ValueError, match="no valid 'answer'"):
        card.save_cards(deck_id, [bad_card])


def test_save_cards_is_all_or_nothing(db_path):
    deck_id = deck.create_deck("Biology")
    cards = [
        {"question": "Good Q", "answer": "Good A"},
        {"question": "Bad Q"},
    ]

    with pytest.raises(ValueError):
        card.save_cards(deck_id, cards)

    assert card.get_cards(deck_id) == []


@pytest.mark.parametrize("bad_id", ["1", None, 1.5, True])
def test_save_cards_rejects_non_integer_deck_id(db_path, bad_id):
    with pytest.raises(ValueError, match="integer"):
        card.save_cards(bad_id, _sample_cards())


def test_save_cards_raises_runtime_error_for_nonexistent_deck(db_path):
    with pytest.raises(RuntimeError, match="deck 9999 may not exist"):
        card.save_cards(9999, _sample_cards())

    assert card.get_cards(9999) == []


def test_save_cards_raises_runtime_error_when_table_missing(empty_db):
    with pytest.raises(RuntimeError, match="Failed to save cards"):
        card.save_cards(1, _sample_cards())


def test_save_cards_raises_runtime_error_when_db_unopenable(unopenable_db):
    with pytest.raises(RuntimeError, match="Could not open database"):
        card.save_cards(1, _sample_cards())


# ---------------------------------------------------------------------------
# card.get_cards
# ---------------------------------------------------------------------------


def test_get_cards_returns_full_card_dicts(db_path):
    deck_id = deck.create_deck("Biology")
    card.save_cards(deck_id, [{"question": "What is ATP?", "answer": "Energy."}])

    result = card.get_cards(deck_id)

    assert result == [
        {
            "id": 1,
            "deck_id": deck_id,
            "question": "What is ATP?",
            "answer": "Energy.",
            "difficulty": "medium",
            "next_review_date": None,
        }
    ]


def test_get_cards_returns_cards_in_saved_order(db_path):
    deck_id = deck.create_deck("Biology")
    card.save_cards(deck_id, _sample_cards())

    questions = [c["question"] for c in card.get_cards(deck_id)]

    assert questions == ["What is ATP?", "What is DNA?"]


def test_get_cards_only_returns_cards_for_requested_deck(db_path):
    first = deck.create_deck("First")
    second = deck.create_deck("Second")
    card.save_cards(first, [{"question": "Q1", "answer": "A1"}])
    card.save_cards(second, [{"question": "Q2", "answer": "A2"}])

    result = card.get_cards(second)

    assert len(result) == 1
    assert result[0]["question"] == "Q2"
    assert result[0]["deck_id"] == second


def test_get_cards_returns_empty_list_for_deck_without_cards(db_path):
    deck_id = deck.create_deck("Empty")

    assert card.get_cards(deck_id) == []


def test_get_cards_returns_empty_list_for_unknown_deck(db_path):
    assert card.get_cards(9999) == []


@pytest.mark.parametrize("bad_id", ["1", None, 1.5, True])
def test_get_cards_rejects_non_integer_deck_id(db_path, bad_id):
    with pytest.raises(ValueError, match="integer"):
        card.get_cards(bad_id)


def test_get_cards_raises_runtime_error_when_table_missing(empty_db):
    with pytest.raises(RuntimeError, match="Failed to fetch cards"):
        card.get_cards(1)


def test_get_cards_raises_runtime_error_when_db_unopenable(unopenable_db):
    with pytest.raises(RuntimeError, match="Could not open database"):
        card.get_cards(1)


# ---------------------------------------------------------------------------
# Shared behaviour
# ---------------------------------------------------------------------------


def test_models_use_default_path_when_env_var_not_set(monkeypatch):
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    opened = []

    def fake_connect(path):
        opened.append(path)
        raise sqlite3.OperationalError("blocked for test")

    monkeypatch.setattr(sqlite3, "connect", fake_connect)

    with pytest.raises(RuntimeError):
        deck.get_deck(1)
    with pytest.raises(RuntimeError):
        card.get_cards(1)

    assert opened == [str(_REAL_DB_PATH), str(_REAL_DB_PATH)]
