from engram_ai import Forge
from engram_ai.models.skill import Skill


def test_skill_has_prediction_fields():
    skill = Skill(
        rule="test",
        context_pattern="ctx",
        confidence=0.8,
        source_experiences=[],
        evidence_count=0,
        valence_summary={},
    )
    assert skill.prediction_hits == 0
    assert skill.prediction_misses == 0


def test_skill_prediction_fields_settable():
    skill = Skill(
        rule="test",
        context_pattern="ctx",
        confidence=0.8,
        source_experiences=[],
        evidence_count=0,
        valence_summary={},
        prediction_hits=5,
        prediction_misses=2,
    )
    assert skill.prediction_hits == 5
    assert skill.prediction_misses == 2


def test_check_skill_effectiveness_positive_hit(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="Use eager loading",
        context_pattern="database queries",
        confidence=0.8,
        source_experiences=["exp1"],
        evidence_count=1,
        valence_summary={"positive": 1},
    )
    forge._storage.store_skill(skill)
    forge._storage.mark_skills_applied([skill.id])

    from engram_ai.models.experience import Experience
    exp = Experience(
        action="Used eager loading",
        context="database queries optimization",
        outcome="Faster queries",
        valence=0.8,
    )
    forge.check_skill_effectiveness(exp)
    all_skills = forge._storage.get_all_skills()
    target = [s for s in all_skills if s.id == skill.id][0]
    assert target.prediction_hits >= 1


def test_check_skill_effectiveness_negative_miss(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="Use eager loading",
        context_pattern="database queries",
        confidence=0.8,
        source_experiences=["exp1"],
        evidence_count=1,
        valence_summary={"positive": 1},
    )
    forge._storage.store_skill(skill)
    forge._storage.mark_skills_applied([skill.id])

    from engram_ai.models.experience import Experience
    exp = Experience(
        action="Used eager loading",
        context="database queries optimization",
        outcome="Still slow",
        valence=-0.5,
    )
    forge.check_skill_effectiveness(exp)
    all_skills = forge._storage.get_all_skills()
    target = [s for s in all_skills if s.id == skill.id][0]
    assert target.prediction_misses >= 1


def test_check_skill_effectiveness_confidence_drop(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="Use eager loading",
        context_pattern="database queries",
        confidence=0.8,
        source_experiences=["exp1"],
        evidence_count=1,
        valence_summary={"positive": 1},
        prediction_hits=0,
        prediction_misses=2,
    )
    forge._storage.store_skill(skill)
    forge._storage.mark_skills_applied([skill.id])

    from engram_ai.models.experience import Experience
    exp = Experience(
        action="Used eager loading",
        context="database queries optimization",
        outcome="Failed again",
        valence=-0.5,
    )
    updated = forge.check_skill_effectiveness(exp)
    assert len(updated) >= 1
    assert updated[0].confidence < 0.8


def test_record_calls_check_effectiveness(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="test skill",
        context_pattern="test context",
        confidence=0.8,
        source_experiences=["exp1"],
        evidence_count=1,
        valence_summary={},
    )
    forge._storage.store_skill(skill)
    forge._storage.mark_skills_applied([skill.id])
    forge.record(
        action="test action",
        context="test context situation",
        outcome="good result",
        valence=0.8,
    )
    all_skills = forge._storage.get_all_skills()
    target = [s for s in all_skills if s.id == skill.id][0]
    assert target is not None
