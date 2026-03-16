# tests/models/test_skill.py
import pytest
from datetime import datetime

def test_skill_creation():
    from engram_ai.models.skill import Skill
    skill = Skill(rule="Avoid Optional in API responses", context_pattern="API response type design", confidence=0.85, source_experiences=["exp_001", "exp_002", "exp_003"], evidence_count=3, valence_summary={"positive": 2, "negative": 1})
    assert skill.rule == "Avoid Optional in API responses"
    assert skill.confidence == 0.85
    assert len(skill.source_experiences) == 3
    assert skill.schema_version == 1
    assert skill.id
    assert isinstance(skill.created_at, datetime)

def test_skill_confidence_bounds():
    from engram_ai.models.skill import Skill
    with pytest.raises(Exception):
        Skill(rule="r", context_pattern="c", confidence=1.5, source_experiences=[], evidence_count=0, valence_summary={})
    with pytest.raises(Exception):
        Skill(rule="r", context_pattern="c", confidence=-0.1, source_experiences=[], evidence_count=0, valence_summary={})

def test_skill_serialization_roundtrip():
    from engram_ai.models.skill import Skill
    skill = Skill(rule="test rule", context_pattern="test pattern", confidence=0.7, source_experiences=["a", "b"], evidence_count=2, valence_summary={"positive": 2, "negative": 0})
    data = skill.model_dump()
    restored = Skill(**data)
    assert restored.id == skill.id
    assert restored.rule == skill.rule
