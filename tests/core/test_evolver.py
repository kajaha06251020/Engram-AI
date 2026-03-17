import pytest
from engram_ai.models.skill import Skill

@pytest.fixture
def storage(tmp_path):
    from engram_ai.storage.chromadb import ChromaDBStorage
    return ChromaDBStorage(persist_path=str(tmp_path / "db"))

@pytest.fixture
def bus():
    from engram_ai.events.bus import EventBus
    return EventBus()

@pytest.fixture
def mock_llm():
    from tests.conftest import MockLLM
    llm = MockLLM()
    llm.set_evolve_response("- Avoid Optional in API responses (confidence: 0.85)\n- Use default values for all fields (confidence: 0.80)\n")
    return llm

@pytest.fixture
def adapter():
    from engram_ai.adapters.claude_code import ClaudeCodeAdapter
    return ClaudeCodeAdapter()

@pytest.fixture
def evolver(storage, bus, mock_llm, adapter):
    from engram_ai.core.evolver import Evolver
    return Evolver(storage=storage, event_bus=bus, llm=mock_llm, adapter=adapter)

def _seed_skills(storage):
    skills = [
        Skill(rule="Avoid Optional", context_pattern="API design", confidence=0.85, source_experiences=["e1"], evidence_count=1, valence_summary={"positive": 1, "negative": 0}),
        Skill(rule="Use defaults", context_pattern="API design", confidence=0.80, source_experiences=["e2"], evidence_count=1, valence_summary={"positive": 1, "negative": 0}),
    ]
    for s in skills:
        storage.store_skill(s)
    return skills

def test_evolve_writes_to_config(storage, evolver, tmp_path):
    _seed_skills(storage)
    config_path = str(tmp_path / "CLAUDE.md")
    (tmp_path / "CLAUDE.md").write_text("# Rules\n", encoding="utf-8")
    evolver.evolve(config_path=config_path)
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "# Rules" in content
    assert "<!-- engram-ai:start -->" in content
    assert "Avoid Optional" in content

def test_evolve_marks_skills_applied(storage, evolver, tmp_path):
    _seed_skills(storage)
    config_path = str(tmp_path / "CLAUDE.md")
    (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
    evolver.evolve(config_path=config_path)
    unapplied = storage.get_unapplied_skills()
    assert len(unapplied) == 0

def test_evolve_emits_event(storage, evolver, bus, tmp_path):
    _seed_skills(storage)
    config_path = str(tmp_path / "CLAUDE.md")
    (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
    received = []
    bus.on("agent.evolved", lambda p: received.append(p))
    evolver.evolve(config_path=config_path)
    assert len(received) == 1

def test_evolve_with_no_unapplied_skills(storage, evolver, tmp_path):
    config_path = str(tmp_path / "CLAUDE.md")
    (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
    record = evolver.evolve(config_path=config_path)
    assert record is None

def test_evolve_idempotent(storage, evolver, mock_llm, tmp_path):
    _seed_skills(storage)
    config_path = str(tmp_path / "CLAUDE.md")
    (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
    evolver.evolve(config_path=config_path)
    more_skill = Skill(rule="New skill", context_pattern="new pattern", confidence=0.9, source_experiences=["e3"], evidence_count=1, valence_summary={"positive": 1, "negative": 0})
    storage.store_skill(more_skill)
    mock_llm.set_evolve_response("- New skill (confidence: 0.9)\n")
    evolver.evolve(config_path=config_path)
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert content.count("<!-- engram-ai:start -->") == 1


def test_evolve_separates_positive_and_anti(tmp_path, mock_llm):
    from engram_ai.core.evolver import Evolver
    from engram_ai.events.bus import EventBus
    from engram_ai.adapters.claude_code import ClaudeCodeAdapter
    from engram_ai.storage.chromadb import ChromaDBStorage

    storage = ChromaDBStorage(persist_path=str(tmp_path / "db"))
    bus = EventBus()
    adapter = ClaudeCodeAdapter()
    mock_llm.set_evolve_response("- Skill content")
    evolver = Evolver(storage, bus, mock_llm, adapter)
    config_path = str(tmp_path / "CLAUDE.md")

    # Store one positive and one anti skill
    pos_skill = Skill(
        rule="Use validation", context_pattern="API", confidence=0.8,
        source_experiences=["e1"], evidence_count=1,
        valence_summary={"positive": 3, "negative": 0}, skill_type="positive",
    )
    anti_skill = Skill(
        rule="Never use eval", context_pattern="Security", confidence=0.9,
        source_experiences=["e2"], evidence_count=1,
        valence_summary={"positive": 0, "negative": 4}, skill_type="anti",
    )
    storage.store_skill(pos_skill)
    storage.store_skill(anti_skill)

    record = evolver.evolve(config_path)
    assert record is not None
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "<!-- engram-ai:start -->" in content
    assert "<!-- engram-ai:anti-skills:start -->" in content
    # Both skills marked applied
    assert len(storage.get_unapplied_skills()) == 0
