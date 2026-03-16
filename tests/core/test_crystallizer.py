import pytest
from engram_ai.models.experience import Experience
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
    llm.set_crystallize_response([Skill(
        rule="Avoid Optional in API responses", context_pattern="API design",
        confidence=0.85, source_experiences=["e1", "e2", "e3"],
        evidence_count=3, valence_summary={"positive": 2, "negative": 1})])
    return llm

@pytest.fixture
def crystallizer(storage, bus, mock_llm):
    from engram_ai.core.crystallizer import Crystallizer
    return Crystallizer(storage=storage, event_bus=bus, llm=mock_llm)

def _seed_similar_experiences(storage):
    for i in range(5):
        storage.store_experience(Experience(
            action=f"Used Optional type in API field {i}",
            context="Designing API response model",
            outcome="User requested removal of null values" if i % 2 == 0 else "User approved",
            valence=-0.8 if i % 2 == 0 else 0.9))

def test_crystallize_produces_skills(storage, crystallizer):
    _seed_similar_experiences(storage)
    skills = crystallizer.crystallize(min_experiences=3)
    assert len(skills) >= 1
    assert skills[0].rule == "Avoid Optional in API responses"

def test_crystallize_emits_event(storage, crystallizer, bus):
    _seed_similar_experiences(storage)
    received = []
    bus.on("skill.crystallized", lambda p: received.append(p))
    crystallizer.crystallize(min_experiences=3)
    assert len(received) >= 1

def test_crystallize_stores_skills(storage, crystallizer):
    _seed_similar_experiences(storage)
    crystallizer.crystallize(min_experiences=3)
    skills = storage.get_all_skills()
    assert len(skills) >= 1

def test_crystallize_with_insufficient_experiences(storage, crystallizer):
    storage.store_experience(Experience(action="solo action", context="unique context", outcome="outcome", valence=0.5))
    skills = crystallizer.crystallize(min_experiences=3)
    assert skills == []
