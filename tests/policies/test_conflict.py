from engram_ai.events.bus import EventBus
from engram_ai.events.events import SKILL_CRYSTALLIZED, SKILL_CONFLICT_DETECTED
from engram_ai.models.skill import Skill
from engram_ai.policies.conflict import ConflictPolicy


def _make_skill(rule="test", confidence=0.8, valence_summary=None, **kw):
    return Skill(
        rule=rule, context_pattern="test", confidence=confidence,
        source_experiences=["e1"], evidence_count=1,
        valence_summary=valence_summary or {"positive": 3, "negative": 0},
        **kw,
    )


class FakeStorage:
    def __init__(self):
        self._skills = []
        self._updated = []

    def add_skill(self, skill):
        self._skills.append(skill)

    def store_skill(self, skill):
        self._skills.append(skill)
        return skill.id

    def get_all_skills(self):
        return [s for s in self._skills if s.status == "active"]

    def query_skills(self, text, k=5):
        return [(s, 0.5) for s in self._skills[:k] if s.status == "active"]

    def update_skill(self, skill):
        self._updated.append(skill)
        for i, s in enumerate(self._skills):
            if s.id == skill.id:
                self._skills[i] = skill


class FakeLLM:
    def __init__(self, verify_result=True):
        self._verify_result = verify_result

    def verify_conflict(self, a, b):
        return self._verify_result

    def merge_skills(self, a, b):
        return _make_skill(
            rule=f"Merged: {a.rule} + {b.rule}",
            confidence=max(a.confidence, b.confidence),
        )


def test_auto_detect_on_crystallize():
    storage = FakeStorage()
    bus = EventBus()
    llm = FakeLLM(verify_result=True)
    events = []
    bus.on(SKILL_CONFLICT_DETECTED, lambda payload: events.append(payload))
    # Existing positive skill
    existing = _make_skill(rule="Always use ORM", valence_summary={"positive": 5, "negative": 0})
    storage.add_skill(existing)
    ConflictPolicy(storage, bus, llm)
    # New contradicting skill — add to storage first (matches production: store then emit)
    new_skill = _make_skill(rule="Never use ORM", valence_summary={"positive": 0, "negative": 4})
    storage.add_skill(new_skill)
    bus.emit(SKILL_CRYSTALLIZED, new_skill)
    assert len(events) == 1
    assert events[0]["skill_a"].id == new_skill.id


def test_no_conflict_when_same_direction():
    storage = FakeStorage()
    bus = EventBus()
    llm = FakeLLM(verify_result=True)
    events = []
    bus.on(SKILL_CONFLICT_DETECTED, lambda payload: events.append(payload))
    existing = _make_skill(rule="Use type hints", valence_summary={"positive": 5, "negative": 0})
    storage.add_skill(existing)
    ConflictPolicy(storage, bus, llm)
    new_skill = _make_skill(rule="Use docstrings", valence_summary={"positive": 4, "negative": 0})
    bus.emit(SKILL_CRYSTALLIZED, new_skill)
    assert len(events) == 0  # same direction, no conflict


def test_detect_all_conflicts_no_llm():
    storage = FakeStorage()
    bus = EventBus()
    llm = FakeLLM()
    s1 = _make_skill(rule="Always use ORM", valence_summary={"positive": 5, "negative": 0})
    s2 = _make_skill(rule="Never use ORM", valence_summary={"positive": 0, "negative": 4})
    storage.add_skill(s1)
    storage.add_skill(s2)
    policy = ConflictPolicy(storage, bus, llm)
    conflicts = policy.detect_all_conflicts()
    assert len(conflicts) >= 1


def test_auto_merge():
    storage = FakeStorage()
    bus = EventBus()
    llm = FakeLLM()
    s1 = _make_skill(rule="Use ORM")
    s2 = _make_skill(rule="Use raw SQL")
    storage.add_skill(s1)
    storage.add_skill(s2)
    policy = ConflictPolicy(storage, bus, llm)
    merged = policy.auto_merge(s1.id, s2.id)
    assert "Merged" in merged.rule
    # Originals are superseded
    assert any(s.status == "superseded" and s.id == s1.id for s in storage._skills)
    assert any(s.status == "superseded" and s.id == s2.id for s in storage._skills)
