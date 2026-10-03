"""AI service: the only file in this project allowed to call the Gemini API."""

import json
import os

from google import genai

_MODEL_NAME = "gemini-3.8-flash"

_PROMPT_TEMPLATE = """You are helping a student study. Read the text below and
generate 5 to 10 flashcards from it. Each flashcard must have a short
"question" and a concise "answer".

Return ONLY valid JSON, with no markdown formatting and no extra text,
in exactly this shape:

[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]

Text to generate flashcards from:
---
{text}
---
"""


def _get_client() -> "genai.Client":
    """Create and return the Gemini API client.

    Raises:
        RuntimeError: If GEMINI_API_KEY is not set in the environment.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )
    return genai.Client(api_key=api_key)


def generate_flashcards(text: str) -> list[dict]:
    """Call the Gemini API and return a list of {question, answer} dicts.

    Args:
        text: Raw study text pasted by the user.

    Returns:
        A list of dicts, each with "question" and "answer" keys.

    Raises:
        ValueError: If text is empty, or the API response is not valid
            JSON in the expected shape.
        RuntimeError: If the Gemini API call itself fails.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string.")

    client = _get_client()
    prompt = _PROMPT_TEMPLATE.format(text=text.strip())

    try:
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=prompt,
        )
        raw_output = response.text
    except Exception as exc:  # the Gemini SDK can raise several exception types
        raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini did not return valid JSON: {exc}. Raw output: {raw_output[:200]}"
        ) from exc

    if not isinstance(parsed, list) or not parsed:
        raise ValueError("Gemini response JSON was not a non-empty list.")

    cards: list[dict] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            raise ValueError(f"Item {index} in Gemini response is not an object.")
        question = item.get("question")
        answer = item.get("answer")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Item {index} is missing a valid 'question'.")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError(f"Item {index} is missing a valid 'answer'.")
        cards.append({"question": question.strip(), "answer": answer.strip()})

    return cards