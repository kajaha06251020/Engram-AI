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
