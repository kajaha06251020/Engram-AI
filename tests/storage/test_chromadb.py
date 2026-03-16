import pytest
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill

@pytest.fixture
def storage(tmp_path):
    from engram_ai.storage.chromadb import ChromaDBStorage
    return ChromaDBStorage(persist_path=str(tmp_path / "test_db"))

def test_store_and_retrieve_experience(storage):
    exp = Experience(action="Used Optional", context="API design", outcome="User complained", valence=-0.8)
    storage.store_experience(exp)
    results = storage.query_experiences("API design", k=5)
    assert len(results) >= 1
    assert results[0][0].id == exp.id

def test_query_returns_similarity_scores(storage):
    exp = Experience(action="Set defaults", context="API response design", outcome="User approved", valence=1.0)
    storage.store_experience(exp)
    results = storage.query_experiences("API response", k=5)
    assert len(results) >= 1
    _, similarity = results[0]
    assert 0.0 <= similarity <= 1.0

def test_store_and_retrieve_skill(storage):
    skill = Skill(rule="Avoid Optional", context_pattern="API design", confidence=0.85, source_experiences=["e1", "e2"], evidence_count=2, valence_summary={"positive": 1, "negative": 1})
    storage.store_skill(skill)
    skills = storage.get_all_skills()
    assert len(skills) == 1
    assert skills[0].id == skill.id

def test_get_all_experiences(storage):
    for i in range(3):
        storage.store_experience(Experience(action=f"action_{i}", context=f"context_{i}", outcome=f"outcome_{i}", valence=0.5))
    all_exp = storage.get_all_experiences()
    assert len(all_exp) == 3

def test_query_empty_storage(storage):
    results = storage.query_experiences("anything", k=5)
    assert results == []

def test_get_unapplied_skills(storage):
    skill1 = Skill(rule="rule1", context_pattern="p", confidence=0.8, source_experiences=[], evidence_count=0, valence_summary={})
    skill2 = Skill(rule="rule2", context_pattern="p", confidence=0.8, source_experiences=[], evidence_count=0, valence_summary={})
    storage.store_skill(skill1)
    storage.store_skill(skill2)
    storage.mark_skills_applied([skill1.id])
    unapplied = storage.get_unapplied_skills()
    assert len(unapplied) == 1
    assert unapplied[0].id == skill2.id
