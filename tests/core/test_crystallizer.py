import pytest
from engram_ai.core.crystallizer import Crystallizer
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


class FakeStorageForReinforcement:
    """Fake storage with deterministic query_skills similarity."""
    def __init__(self):
        self._experiences = []
        self._skills = []
        self._updated = []

    def store_experience(self, exp):
        self._experiences.append(exp)
        return exp.id

    def get_all_experiences(self):
        return list(self._experiences)

    def query_experiences(self, context, k=5):
        # Return all with high similarity for clustering
        return [(e, 0.8) for e in self._experiences[:k]]

    def store_skill(self, skill):
        self._skills.append(skill)
        return skill.id

    def get_all_skills(self):
        return [s for s in self._skills if s.status == "active"]

    def query_skills(self, text, k=5):
        # Return existing skills with similarity above REINFORCEMENT_THRESHOLD
        return [(s, 0.6) for s in self._skills[:k] if s.status == "active"]

    def update_skill(self, skill):
        self._updated.append(skill)
        for i, s in enumerate(self._skills):
            if s.id == skill.id:
                self._skills[i] = skill


def test_reinforcement_bumps_existing_skill(mock_llm):
    from engram_ai.events.bus import EventBus
    from engram_ai.events.events import SKILL_REINFORCED

    storage = FakeStorageForReinforcement()
    bus = EventBus()
    reinforced_events = []
    bus.on(SKILL_REINFORCED, lambda s: reinforced_events.append(s))

    # Pre-existing skill
    existing = Skill(
        rule="Always validate API input", context_pattern="API",
        confidence=0.75, source_experiences=["old1"],
        evidence_count=1, valence_summary={"positive": 3, "negative": 0},
    )
    storage.store_skill(existing)

    # Mock LLM returns a similar skill (would be new, but matches existing)
    similar_skill = Skill(
        rule="Always validate API input schemas", context_pattern="API",
        confidence=0.8, source_experiences=["new1", "new2", "new3"],
        evidence_count=3, valence_summary={"positive": 3, "negative": 0},
    )
    mock_llm.set_crystallize_response([similar_skill])

    # Add enough experiences for clustering
    for i in range(5):
        storage.store_experience(
            Experience(action=f"validate input {i}", context="API validation", outcome="success", valence=0.9)
        )

    crystallizer = Crystallizer(storage, bus, mock_llm)
    crystallizer.crystallize(min_experiences=3, min_confidence=0.5)

    # Should NOT create new skill — reinforced existing instead
    all_skills = storage.get_all_skills()
    assert len(all_skills) == 1  # still just the existing one
    assert all_skills[0].confidence >= 0.85  # bumped from 0.75
    assert all_skills[0].reinforcement_count >= 1
    assert len(reinforced_events) >= 1
