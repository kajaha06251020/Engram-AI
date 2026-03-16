# tests/models/test_evolution.py
from datetime import datetime

def test_evolution_record_creation():
    from engram_ai.models.evolution import EvolutionRecord
    record = EvolutionRecord(skills_applied=["skill_001", "skill_002"], config_path="./CLAUDE.md", diff="+ 2 skills added")
    assert len(record.skills_applied) == 2
    assert record.config_path == "./CLAUDE.md"
    assert record.schema_version == 1
    assert record.id
    assert isinstance(record.timestamp, datetime)

def test_evolution_record_serialization():
    from engram_ai.models.evolution import EvolutionRecord
    record = EvolutionRecord(skills_applied=["s1"], config_path="./CLAUDE.md", diff="+ 1 skill")
    data = record.model_dump()
    restored = EvolutionRecord(**data)
    assert restored.id == record.id
