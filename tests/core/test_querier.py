import pytest
from engram_ai.models.experience import Experience

@pytest.fixture
def storage(tmp_path):
    from engram_ai.storage.chromadb import ChromaDBStorage
    return ChromaDBStorage(persist_path=str(tmp_path / "db"))

@pytest.fixture
def querier(storage):
    from engram_ai.core.querier import Querier
    return Querier(storage=storage)

def _seed_experiences(storage):
    experiences = [
        Experience(action="Used Optional", context="API design", outcome="User complained", valence=-0.8),
        Experience(action="Set defaults", context="API design", outcome="User approved", valence=1.0),
        Experience(action="Added tests", context="Testing phase", outcome="All passed", valence=0.9),
    ]
    for exp in experiences:
        storage.store_experience(exp)

def test_query_returns_best_and_avoid(storage, querier):
    _seed_experiences(storage)
    result = querier.query("API response design", k=5)
    assert "best" in result
    assert "avoid" in result

def test_best_has_positive_valence(storage, querier):
    _seed_experiences(storage)
    result = querier.query("API design", k=5)
    for exp, score in result["best"]:
        assert exp.valence > 0

def test_avoid_has_negative_valence(storage, querier):
    _seed_experiences(storage)
    result = querier.query("API design", k=5)
    for exp, score in result["avoid"]:
        assert exp.valence < 0

def test_query_empty_storage(storage, querier):
    result = querier.query("anything", k=5)
    assert result["best"] == []
    assert result["avoid"] == []
