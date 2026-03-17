from datetime import datetime, timedelta
from engram_ai.events.bus import EventBus
from engram_ai.events.events import EXPERIENCE_RECORDED, SKILL_DECAYED
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill
from engram_ai.policies.decay import DecayPolicy


def _make_skill(confidence=0.8, created_days_ago=0, last_reinforced_days_ago=None, **kw):
    defaults = dict(
        rule="test rule", context_pattern="test",
        source_experiences=["e1"], evidence_count=1,
        valence_summary={"positive": 3, "negative": 0},
        confidence=confidence,
        created_at=datetime.now() - timedelta(days=created_days_ago),
    )
    if last_reinforced_days_ago is not None:
        defaults["last_reinforced_at"] = datetime.now() - timedelta(days=last_reinforced_days_ago)
    defaults.update(kw)
    return Skill(**defaults)


class FakeStorage:
    def __init__(self):
        self._skills = []
        self._updated = []

    def add_skill(self, skill):
        self._skills.append(skill)

    def get_all_skills(self):
        return list(self._skills)

    def query_skills(self, text, k=5):
        return [(s, 0.5) for s in self._skills[:k]]

    def update_skill(self, skill):
        self._updated.append(skill)
        for i, s in enumerate(self._skills):
            if s.id == skill.id:
                self._skills[i] = skill


def test_time_decay_formula():
    """90-day half-life: skill created 90 days ago -> confidence halved."""
    storage = FakeStorage()
    bus = EventBus()
    skill = _make_skill(confidence=0.8, created_days_ago=90)
    storage.add_skill(skill)
    policy = DecayPolicy(storage, bus)
    decayed = policy.apply_time_decay()
    assert len(decayed) == 1
    assert abs(decayed[0].confidence - 0.4) < 0.05


def test_time_decay_uses_last_reinforced():
    """If last_reinforced_at is set, decay from that date."""
    storage = FakeStorage()
    bus = EventBus()
    skill = _make_skill(confidence=0.8, created_days_ago=180, last_reinforced_days_ago=10)
    storage.add_skill(skill)
    policy = DecayPolicy(storage, bus)
    decayed = policy.apply_time_decay()
    # 10 days is much less than 90-day half-life, so barely decays
    assert decayed[0].confidence > 0.7


def test_time_decay_emits_event_below_threshold():
    storage = FakeStorage()
    bus = EventBus()
    events = []
    bus.on(SKILL_DECAYED, lambda s: events.append(s))
    skill = _make_skill(confidence=0.15, created_days_ago=180)
    storage.add_skill(skill)
    policy = DecayPolicy(storage, bus)
    policy.apply_time_decay()
    assert len(events) == 1


def test_event_decay_on_negative_experience():
    storage = FakeStorage()
    bus = EventBus()
    # Positive skill
    skill = _make_skill(confidence=0.8, rule="Always use caching")
    storage.add_skill(skill)
    DecayPolicy(storage, bus)
    # Record a negative experience with context that matches the skill
    exp = Experience(action="used cache", context="caching strategy", outcome="broke", valence=-0.8)
    bus.emit(EXPERIENCE_RECORDED, exp)
    assert len(storage._updated) == 1
    assert storage._updated[0].confidence < 0.8


def test_event_decay_ignores_mildly_negative():
    storage = FakeStorage()
    bus = EventBus()
    skill = _make_skill(confidence=0.8)
    storage.add_skill(skill)
    DecayPolicy(storage, bus)
    exp = Experience(action="a", context="c", outcome="o", valence=-0.1)
    bus.emit(EXPERIENCE_RECORDED, exp)
    assert len(storage._updated) == 0  # -0.1 > -0.3 threshold, no decay
