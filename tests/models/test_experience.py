# tests/models/test_experience.py
import pytest
from datetime import datetime

def test_experience_creation_with_required_fields():
    from engram_ai.models.experience import Experience
    exp = Experience(action="Used Optional fields", context="API design", outcome="User requested fix", valence=-0.8)
    assert exp.action == "Used Optional fields"
    assert exp.context == "API design"
    assert exp.outcome == "User requested fix"
    assert exp.valence == -0.8
    assert exp.status == "complete"
    assert exp.schema_version == 1
    assert exp.id
    assert isinstance(exp.timestamp, datetime)
    assert exp.metadata == {}

def test_experience_pending_status():
    from engram_ai.models.experience import Experience
    exp = Experience(action="Edited file", context="Coding", outcome="", valence=0.0, status="pending")
    assert exp.status == "pending"

def test_experience_valence_upper_bound():
    from engram_ai.models.experience import Experience
    with pytest.raises(Exception):
        Experience(action="a", context="b", outcome="c", valence=1.5)

def test_experience_valence_lower_bound():
    from engram_ai.models.experience import Experience
    with pytest.raises(Exception):
        Experience(action="a", context="b", outcome="c", valence=-1.5)

def test_experience_serialization_roundtrip():
    from engram_ai.models.experience import Experience
    exp = Experience(action="test action", context="test context", outcome="test outcome", valence=0.5, metadata={"tool": "Edit", "file": "main.py"})
    data = exp.model_dump()
    restored = Experience(**data)
    assert restored.id == exp.id
    assert restored.action == exp.action
    assert restored.valence == exp.valence
    assert restored.metadata == exp.metadata

def test_experience_json_roundtrip():
    from engram_ai.models.experience import Experience
    exp = Experience(action="test", context="ctx", outcome="out", valence=0.0)
    json_str = exp.model_dump_json()
    restored = Experience.model_validate_json(json_str)
    assert restored.id == exp.id
