"""Tests for backend/services/ai_service.py. The real Gemini API is never
called here -- client.models.generate_content() is mocked in every test."""

from unittest.mock import MagicMock, patch

import pytest

from backend.services import ai_service


@pytest.fixture(autouse=True)
def fake_api_key(monkeypatch):
    """Ensure GEMINI_API_KEY is always set during tests."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")


def _mock_client_with_response(text: str) -> MagicMock:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = text
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


@patch("backend.services.ai_service.genai.Client")
def test_generate_flashcards_valid_response(mock_client_cls):
    mock_client_cls.return_value = _mock_client_with_response(
        '[{"question": "What is 2+2?", "answer": "4"}, '
        '{"question": "Capital of France?", "answer": "Paris"}]'
    )

    result = ai_service.generate_flashcards("Some notes about math and geography.")

    assert len(result) == 2
    assert result[0] == {"question": "What is 2+2?", "answer": "4"}


@patch("backend.services.ai_service.genai.Client")
def test_generate_flashcards_strips_markdown_fences(mock_client_cls):
    mock_client_cls.return_value = _mock_client_with_response(
        '```json\n[{"question": "Q1", "answer": "A1"}]\n```'
    )

    result = ai_service.generate_flashcards("Some notes.")

    assert result == [{"question": "Q1", "answer": "A1"}]


@patch("backend.services.ai_service.genai.Client")
def test_generate_flashcards_malformed_json_raises(mock_client_cls):
    mock_client_cls.return_value = _mock_client_with_response("not valid json at all")

    with pytest.raises(ValueError):
        ai_service.generate_flashcards("Some notes.")


@patch("backend.services.ai_service.genai.Client")
def test_generate_flashcards_empty_list_raises(mock_client_cls):
    mock_client_cls.return_value = _mock_client_with_response("[]")

    with pytest.raises(ValueError):
        ai_service.generate_flashcards("Some notes.")


@patch("backend.services.ai_service.genai.Client")
def test_generate_flashcards_missing_fields_raises(mock_client_cls):
    mock_client_cls.return_value = _mock_client_with_response(
        '[{"question": "Only a question, no answer"}]'
    )

    with pytest.raises(ValueError):
        ai_service.generate_flashcards("Some notes.")


@patch("backend.services.ai_service.genai.Client")
def test_generate_flashcards_api_failure_raises_runtime_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("network error")
    mock_client_cls.return_value = mock_client

    with pytest.raises(RuntimeError):
        ai_service.generate_flashcards("Some notes.")


def test_generate_flashcards_empty_text_raises_value_error():
    with pytest.raises(ValueError):
        ai_service.generate_flashcards("")


def test_generate_flashcards_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        ai_service.generate_flashcards("Some notes.")
