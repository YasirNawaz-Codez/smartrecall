"""Routes for the core flow: paste text -> generate flashcards -> view deck."""

from flask import Blueprint, render_template, request

from backend.models import card as card_model
from backend.models import deck as deck_model
from backend.services import ai_service

flashcards_bp = Blueprint("flashcards", __name__)


@flashcards_bp.route("/", methods=["GET"])
def index():
    """Render the paste-text form (Moustapha's index.html)."""
    return render_template("index.html")


@flashcards_bp.route("/generate", methods=["POST"])
def generate():
    """Read pasted text, generate flashcards, save them, show the deck.

    On any error (bad input, Gemini failure, or database failure), the
    user is sent back to the form with an error message instead of a
    stack trace.
    """
    text = request.form.get("text", "")

    try:
        cards_data = ai_service.generate_flashcards(text)
        deck_id = deck_model.create_deck(_make_deck_name(text))
        card_model.save_cards(deck_id, cards_data)
        deck = deck_model.get_deck(deck_id)
        cards = card_model.get_cards(deck_id)
    except (ValueError, RuntimeError) as exc:
        return render_template("index.html", error=str(exc)), 400

    return render_template("deck.html", deck=deck, cards=cards)


def _make_deck_name(text: str) -> str:
    """Build a short deck name from the first few words of the pasted text."""
    words = text.strip().split()
    snippet = " ".join(words[:6])
    if not snippet:
        return "Untitled Deck"
    return snippet if len(words) <= 6 else snippet + "..."
