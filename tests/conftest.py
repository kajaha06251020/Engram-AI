import pytest
from engram_ai.models.skill import Skill

class MockLLM:
    """Mock LLM that returns fixed responses for testing."""
    def __init__(self):
        self._valence_response = 0.5
        self._crystallize_response = []
        self._evolve_response = ""
        self._verify_conflict_response = True
        self._merge_skills_response = None
        self._extract_experience_response = None

    def set_valence_response(self, valence: float):
        self._valence_response = valence

    def set_crystallize_response(self, skills: list[Skill]):
        self._crystallize_response = skills

    def set_evolve_response(self, text: str):
        self._evolve_response = text

    def detect_valence(self, user_message: str) -> float:
        return self._valence_response

    def crystallize_pattern(self, experiences: list) -> Skill | None:
        if self._crystallize_response:
            return self._crystallize_response.pop(0)
        return None

    def generate_evolution_text(self, skills: list[Skill]) -> str:
        return self._evolve_response

    def set_verify_conflict_response(self, value: bool):
        self._verify_conflict_response = value

    def set_merge_skills_response(self, skill):
        self._merge_skills_response = skill

    def verify_conflict(self, skill_a, skill_b) -> bool:
        return self._verify_conflict_response

    def merge_skills(self, skill_a, skill_b):
        if self._merge_skills_response:
            return self._merge_skills_response
        from engram_ai.models.skill import Skill
        combined = list(set(skill_a.source_experiences + skill_b.source_experiences))
        return Skill(
            rule=f"Merged: {skill_a.rule} + {skill_b.rule}",
            context_pattern=skill_a.context_pattern,
            confidence=max(skill_a.confidence, skill_b.confidence),
            source_experiences=combined,
            evidence_count=skill_a.evidence_count + skill_b.evidence_count,
            valence_summary=skill_a.valence_summary,
        )

    def set_extract_experience_response(self, response: dict | None):
        self._extract_experience_response = response

    def extract_experience(self, messages: list[dict]) -> dict | None:
        return self._extract_experience_response

@pytest.fixture
def mock_llm():
    return MockLLM()
