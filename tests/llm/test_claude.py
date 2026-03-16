import pytest
from unittest.mock import MagicMock, patch
from engram_ai.models.experience import Experience

def test_mock_llm_conforms_to_base():
    from tests.conftest import MockLLM
    llm = MockLLM()
    assert callable(llm.detect_valence)
    assert callable(llm.crystallize_pattern)
    assert callable(llm.generate_evolution_text)

def test_claude_llm_detect_valence_parses_float():
    from engram_ai.llm.claude import ClaudeLLM
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="0.8")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        result = llm.detect_valence("great work!")
        assert result == 0.8

def test_claude_llm_detect_valence_clamps_range():
    from engram_ai.llm.claude import ClaudeLLM
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="5.0")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        assert llm.detect_valence("msg") == 1.0

def test_claude_llm_detect_valence_returns_0_on_parse_error():
    from engram_ai.llm.claude import ClaudeLLM
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not a number")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        assert llm.detect_valence("msg") == 0.0

def test_claude_llm_crystallize_parses_json():
    from engram_ai.llm.claude import ClaudeLLM
    import json
    response_json = json.dumps({"rule": "Use defaults", "context_pattern": "API design", "confidence": 0.9})
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_json)]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        experiences = [Experience(action="a", context="c", outcome="o", valence=0.5) for _ in range(3)]
        skill = llm.crystallize_pattern(experiences)
        assert skill is not None
        assert skill.rule == "Use defaults"
        assert skill.confidence == 0.9

def test_claude_llm_crystallize_returns_none_on_no_pattern():
    from engram_ai.llm.claude import ClaudeLLM
    import json
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({"rule": None}))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        result = llm.crystallize_pattern([Experience(action="a", context="c", outcome="o", valence=0.5)])
        assert result is None
