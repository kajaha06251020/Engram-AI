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

    def generate_evolution_text(self, skills):
        lines = [f"- {s.rule} (confidence: {s.confidence})" for s in skills]
        return "\n".join(lines)


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
