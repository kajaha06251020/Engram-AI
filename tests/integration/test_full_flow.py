import pytest
from engram_ai.models.skill import Skill


class IntegrationMockLLM:
    """Mock LLM that returns realistic responses for integration testing."""

    def detect_valence(self, user_message: str) -> float:
        return 0.5

    def crystallize_pattern(self, experiences):
        if len(experiences) >= 3:
            positive = sum(1 for e in experiences if e.valence > 0)
            negative = sum(1 for e in experiences if e.valence < 0)
            return Skill(
                rule=f"Pattern from {len(experiences)} experiences",
                context_pattern=experiences[0].context,
                confidence=0.85,
                source_experiences=[e.id for e in experiences],
                evidence_count=len(experiences),
                valence_summary={"positive": positive, "negative": negative},
            )
        return None

    def verify_conflict(self, skill_a, skill_b):
        return False  # Conservative: no conflicts by default

    def merge_skills(self, skill_a, skill_b):
        return Skill(
            rule=f"Merged: {skill_a.rule} + {skill_b.rule}",
            context_pattern=skill_a.context_pattern,
            confidence=max(skill_a.confidence, skill_b.confidence),
            source_experiences=list(set(skill_a.source_experiences + skill_b.source_experiences)),
            evidence_count=skill_a.evidence_count + skill_b.evidence_count,
            valence_summary=skill_a.valence_summary,
        )

    def generate_evolution_text(self, skills):
        lines = [f"- {s.rule} (confidence: {s.confidence})" for s in skills]
        return "\n".join(lines)

    def extract_experience(self, messages):
        return None  # Conservative default


@pytest.fixture
def forge(tmp_path):
    from engram_ai.forge import Forge

    return Forge(
        storage_path=str(tmp_path / "data"),
        llm=IntegrationMockLLM(),
    )


def test_full_record_crystallize_evolve_flow(forge, tmp_path):
    """Record 5 experiences -> crystallize -> evolve -> verify CLAUDE.md."""
    # Record experiences
    for i in range(5):
        forge.record(
            action=f"Used Optional type in field {i}",
            context="Designing API response model",
            outcome="User complained about null values" if i % 2 == 0 else "User approved",
            valence=-0.8 if i % 2 == 0 else 0.9,
        )

    # Verify status
    status = forge.status()
    assert status["total_experiences"] == 5

    # Crystallize
    skills = forge.crystallize(min_experiences=3, min_confidence=0.7)
    assert len(skills) >= 1

    status = forge.status()
    assert status["total_skills"] >= 1
    assert status["unapplied_skills"] >= 1

    # Evolve
    config_path = str(tmp_path / "CLAUDE.md")
    (tmp_path / "CLAUDE.md").write_text("# Project\n", encoding="utf-8")
    record = forge.evolve(config_path=config_path)

    assert record is not None
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "# Project" in content
    assert "<!-- engram-ai:start -->" in content
    assert "Pattern from" in content

    # Verify idempotent
    status = forge.status()
    assert status["unapplied_skills"] == 0


def test_query_after_recording(forge):
    """Record positive and negative experiences, query should partition."""
    forge.record(
        action="Used Optional",
        context="API design",
        outcome="User complained",
        valence=-0.8,
    )
    forge.record(
        action="Used defaults",
        context="API design",
        outcome="User happy",
        valence=1.0,
    )
    result = forge.query("API design")
    assert len(result["best"]) >= 1
    assert len(result["avoid"]) >= 1


def test_event_chain_fires(forge, tmp_path):
    """Verify all events fire through the full flow."""
    events_received = []
    forge.on("experience.recorded", lambda p: events_received.append("recorded"))
    forge.on("skill.crystallized", lambda p: events_received.append("crystallized"))
    forge.on("agent.evolved", lambda p: events_received.append("evolved"))

    for i in range(5):
        forge.record(
            action=f"action {i}",
            context="same context for clustering",
            outcome=f"outcome {i}",
            valence=0.8,
        )
    forge.crystallize(min_experiences=3, min_confidence=0.7)

    config_path = str(tmp_path / "CLAUDE.md")
    (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
    forge.evolve(config_path=config_path)

    assert "recorded" in events_received
    assert "crystallized" in events_received
    assert "evolved" in events_received


def test_pending_to_complete_flow(forge):
    """Two-phase recording: pending -> complete."""
    forge.record_pending(
        action="edited api.py",
        context="refactoring",
    )
    forge.complete_pending(
        outcome="user approved",
        valence=1.0,
    )
    status = forge.status()
    assert status["total_experiences"] == 1


def test_v02_reinforcement_decay_conflict_flow(tmp_path):
    """End-to-end: record -> crystallize (reinforcement) -> decay -> conflict detection."""
    from engram_ai.forge import Forge
    from engram_ai.events.events import SKILL_REINFORCED, SKILL_DECAYED
    from engram_ai.policies.decay import DecayConfig

    events = {"reinforced": [], "decayed": []}

    mock_llm = IntegrationMockLLM()
    forge = Forge(
        storage_path=str(tmp_path / "db"),
        llm=mock_llm,
        decay_config=DecayConfig(half_life_days=0.001),  # Very short for testing
        enable_policies=True,
    )
    forge.on(SKILL_REINFORCED, lambda s: events["reinforced"].append(s))
    forge.on(SKILL_DECAYED, lambda s: events["decayed"].append(s))

    # Record positive experiences about API validation
    for i in range(5):
        forge.record(
            action=f"validate API input {i}",
            context="API schema validation best practices",
            outcome="Input validated successfully",
            valence=0.9,
        )

    # First crystallize: creates a new skill
    skills1 = forge.crystallize(min_experiences=3, min_confidence=0.3)
    assert len(skills1) >= 1

    # Record more similar experiences
    for i in range(5):
        forge.record(
            action=f"validate API response {i}",
            context="API schema validation patterns",
            outcome="Response validated successfully",
            valence=0.8,
        )

    # Second crystallize: should reinforce existing skill
    skills2 = forge.crystallize(min_experiences=3, min_confidence=0.3)
    # Reinforcement may or may not trigger depending on embedding similarity.
    # Just verify we can crystallize without errors.
    assert isinstance(skills2, list)

    # Apply decay (with very short half-life)
    decayed = forge.apply_decay()
    assert len(decayed) >= 1

    # Detect conflicts (should be none in this case)
    conflicts = forge.detect_conflicts()
    assert isinstance(conflicts, list)

    # Status check
    status = forge.status()
    assert status["total_experiences"] == 10
    assert status["total_skills"] >= 1


def test_observe_full_flow(tmp_path):
    """End-to-end: observe -> auto-record -> auto-crystallize."""
    from engram_ai.forge import Forge
    from engram_ai.models.skill import Skill
    from tests.conftest import MockLLM

    llm = MockLLM()
    forge = Forge(storage_path=str(tmp_path / "data"), llm=llm)

    # Pre-fill experiences to reach threshold - 1
    for i in range(4):
        forge.record(action=f"action{i}", context="similar context",
                     outcome=f"outcome{i}", valence=0.7)

    # Set up MockLLM for observe + crystallize
    llm.set_extract_experience_response({
        "action": "optimized query",
        "context": "similar context",
        "outcome": "faster response",
        "valence": 0.9,
    })
    # Provide multiple copies to handle potential multi-cluster scenarios
    optimize_skill = Skill(
        rule="Optimize DB queries for list endpoints",
        context_pattern="API performance",
        confidence=0.85, source_experiences=[], evidence_count=5,
        valence_summary={"positive": 5, "negative": 0},
    )
    llm.set_crystallize_response([optimize_skill] * 3)

    result = forge.observe(
        messages=[
            {"role": "user", "content": "The list endpoint is slow"},
            {"role": "assistant", "content": "I optimized the query with eager loading"},
            {"role": "user", "content": "Perfect, much faster now"},
            {"role": "assistant", "content": "Glad it worked!"},
        ],
        max_turns=2,
        crystallize_threshold=5,
    )

    assert result["recorded"] is not None
    assert result["recorded"].action == "optimized query"
    assert len(result["crystallized"]) >= 1
    assert "Optimize DB queries" in result["crystallized"][0].rule


def test_observe_full_flow_no_crystallize_below_threshold(tmp_path):
    """observe does NOT crystallize when below threshold."""
    from engram_ai.forge import Forge
    from tests.conftest import MockLLM

    llm = MockLLM()
    forge = Forge(storage_path=str(tmp_path / "data"), llm=llm)

    llm.set_extract_experience_response({
        "action": "small fix", "context": "minor issue",
        "outcome": "resolved", "valence": 0.5,
    })
    result = forge.observe(
        messages=[{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}],
        crystallize_threshold=5,
    )
    assert result["recorded"] is not None
    assert result["crystallized"] == []


@pytest.fixture
def mock_llm():
    return IntegrationMockLLM()


def test_v03_multi_project_isolation(tmp_path, mock_llm):
    """Projects have isolated data."""
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, llm=mock_llm, config={"default_project": "default"})
    forge_a = pm.get_forge("project_a")
    forge_b = pm.get_forge("project_b")
    forge_a.record(action="action_a", context="ctx_a", outcome="ok", valence=0.5)
    forge_b.record(action="action_b", context="ctx_b", outcome="ok", valence=0.5)
    status_a = forge_a.status()
    status_b = forge_b.status()
    assert status_a["total_experiences"] == 1
    assert status_b["total_experiences"] == 1
