import pytest
from engram_ai.forge import Forge, _trim_messages
from engram_ai.exceptions import EngramError
from tests.conftest import MockLLM


@pytest.fixture
def forge_with_mock(tmp_path):
    llm = MockLLM()
    forge = Forge(storage_path=str(tmp_path / "data"), llm=llm)
    return forge, llm


# --- _trim_messages tests ---

def test_trim_messages_default():
    msgs = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
        {"role": "assistant", "content": "d"},
        {"role": "user", "content": "e"},
        {"role": "assistant", "content": "f"},
    ]
    result = _trim_messages(msgs, max_turns=2)
    assert len(result) == 4
    assert result[0]["content"] == "c"


def test_trim_messages_fewer_than_max():
    msgs = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    result = _trim_messages(msgs, max_turns=5)
    assert len(result) == 2


def test_trim_messages_strips_empty_content():
    msgs = [
        {"role": "user", "content": ""},
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    result = _trim_messages(msgs, max_turns=3)
    assert len(result) == 2
    assert result[0]["content"] == "a"


def test_trim_messages_strips_system_role():
    msgs = [
        {"role": "system", "content": "you are helpful"},
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    result = _trim_messages(msgs, max_turns=3)
    assert len(result) == 2
    assert all(m["role"] in ("user", "assistant") for m in result)


def test_trim_messages_empty_list():
    assert _trim_messages([], max_turns=3) == []


# --- observe() tests ---

def test_observe_records_experience(forge_with_mock):
    forge, llm = forge_with_mock
    llm.set_extract_experience_response({
        "action": "Fixed bug",
        "context": "Login page broken",
        "outcome": "Users can log in",
        "valence": 0.8,
    })
    result = forge.observe([
        {"role": "user", "content": "Login is broken"},
        {"role": "assistant", "content": "I fixed the auth bug"},
    ])
    assert result["recorded"] is not None
    assert result["recorded"].action == "Fixed bug"
    assert result["crystallized"] == []


def test_observe_returns_none_when_no_experience(forge_with_mock):
    forge, llm = forge_with_mock
    llm.set_extract_experience_response(None)
    result = forge.observe([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ])
    assert result["recorded"] is None
    assert result["crystallized"] == []


def test_observe_empty_messages(forge_with_mock):
    forge, llm = forge_with_mock
    result = forge.observe([])
    assert result["recorded"] is None
    assert result["crystallized"] == []


def test_observe_auto_crystallize_at_threshold(forge_with_mock):
    forge, llm = forge_with_mock
    for i in range(4):
        forge.record(action=f"action{i}", context=f"ctx{i}",
                     outcome=f"out{i}", valence=0.5)
    llm.set_extract_experience_response({
        "action": "action4", "context": "ctx4",
        "outcome": "out4", "valence": 0.7,
    })
    result = forge.observe(
        [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}],
        crystallize_threshold=5,
    )
    assert result["recorded"] is not None
    assert result["crystallized"] == []


def test_observe_no_crystallize_below_threshold(forge_with_mock):
    forge, llm = forge_with_mock
    llm.set_extract_experience_response({
        "action": "a", "context": "c", "outcome": "o", "valence": 0.5,
    })
    result = forge.observe(
        [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}],
        crystallize_threshold=5,
    )
    assert result["recorded"] is not None
    assert result["crystallized"] == []


def test_observe_rejects_low_threshold(forge_with_mock):
    forge, llm = forge_with_mock
    with pytest.raises(EngramError, match="crystallize_threshold"):
        forge.observe([{"role": "user", "content": "x"}], crystallize_threshold=1)


def test_observe_raises_on_unsupported_llm(tmp_path):
    from engram_ai.llm.base import BaseLLM

    class MinimalLLM(BaseLLM):
        def detect_valence(self, msg): return 0.0
        def crystallize_pattern(self, exps): return None
        def generate_evolution_text(self, skills): return ""

    forge = Forge(storage_path=str(tmp_path / "data"), llm=MinimalLLM())
    with pytest.raises(EngramError, match="extract_experience"):
        forge.observe([{"role": "user", "content": "x"}])
