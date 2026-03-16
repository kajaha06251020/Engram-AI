import pytest
from engram_ai.models.skill import Skill

class MockLLM:
    """Mock LLM that returns fixed responses for testing."""
    def __init__(self):
        self._valence_response = 0.5
        self._crystallize_response = []
        self._evolve_response = ""

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

@pytest.fixture
def mock_llm():
    return MockLLM()
