import json
import pytest
from unittest.mock import MagicMock, patch
from engram_ai.llm.claude import ClaudeLLM


@pytest.fixture
def claude_llm():
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        llm._client = mock_client
        yield llm


def test_extract_experience_returns_dict(claude_llm):
    response_json = json.dumps({
        "action": "Fixed N+1 query",
        "context": "User API endpoint was slow",
        "outcome": "Response time improved 10x",
        "valence": 0.9,
    })
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_json)]
    claude_llm._client.messages.create.return_value = mock_response
    result = claude_llm.extract_experience([
        {"role": "user", "content": "The API is slow"},
        {"role": "assistant", "content": "I fixed the N+1 query"},
    ])
    assert result is not None
    assert result["action"] == "Fixed N+1 query"
    assert result["valence"] == 0.9


def test_extract_experience_returns_none_for_no_experience(claude_llm):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"experience": null}')]
    claude_llm._client.messages.create.return_value = mock_response
    result = claude_llm.extract_experience([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ])
    assert result is None


def test_extract_experience_clamps_valence(claude_llm):
    response_json = json.dumps({
        "action": "a", "context": "c", "outcome": "o", "valence": 5.0,
    })
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_json)]
    claude_llm._client.messages.create.return_value = mock_response
    result = claude_llm.extract_experience([{"role": "user", "content": "x"}])
    assert result["valence"] == 1.0


def test_extract_experience_returns_none_on_malformed_json(claude_llm):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="not json")]
    claude_llm._client.messages.create.return_value = mock_response
    result = claude_llm.extract_experience([{"role": "user", "content": "x"}])
    assert result is None


def test_extract_experience_returns_none_on_missing_keys(claude_llm):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"action": "a"}')]
    claude_llm._client.messages.create.return_value = mock_response
    result = claude_llm.extract_experience([{"role": "user", "content": "x"}])
    assert result is None
