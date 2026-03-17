from unittest.mock import MagicMock, patch
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill

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



def test_verify_conflict():
    from engram_ai.llm.claude import ClaudeLLM
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="true")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        skill_a = Skill(
            rule="Always use ORM", context_pattern="DB", confidence=0.8,
            source_experiences=["e1"], evidence_count=1,
            valence_summary={"positive": 3, "negative": 0},
        )
        skill_b = Skill(
            rule="Always write raw SQL", context_pattern="DB", confidence=0.7,
            source_experiences=["e2"], evidence_count=1,
            valence_summary={"positive": 2, "negative": 0},
        )
        result = llm.verify_conflict(skill_a, skill_b)
        assert result is True


def test_verify_conflict_false():
    from engram_ai.llm.claude import ClaudeLLM
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="false")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        skill_a = Skill(
            rule="Use type hints", context_pattern="Python", confidence=0.8,
            source_experiences=["e1"], evidence_count=1,
            valence_summary={"positive": 3, "negative": 0},
        )
        skill_b = Skill(
            rule="Write docstrings", context_pattern="Python", confidence=0.7,
            source_experiences=["e2"], evidence_count=1,
            valence_summary={"positive": 2, "negative": 0},
        )
        result = llm.verify_conflict(skill_a, skill_b)
        assert result is False


def test_merge_skills():
    from engram_ai.llm.claude import ClaudeLLM
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"rule": "Use ORM for reads, raw SQL for bulk writes", "context_pattern": "DB", "confidence": 0.85}')]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        skill_a = Skill(
            rule="Always use ORM", context_pattern="DB", confidence=0.8,
            source_experiences=["e1"], evidence_count=1,
            valence_summary={"positive": 3, "negative": 0},
        )
        skill_b = Skill(
            rule="Always write raw SQL", context_pattern="DB", confidence=0.7,
            source_experiences=["e2"], evidence_count=1,
            valence_summary={"positive": 2, "negative": 0},
        )
        merged = llm.merge_skills(skill_a, skill_b)
        assert "ORM" in merged.rule
        assert merged.confidence == 0.85
