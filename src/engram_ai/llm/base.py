from abc import ABC, abstractmethod
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill

class BaseLLM(ABC):
    """Abstract LLM interface for Engram-AI operations."""
    @abstractmethod
    def detect_valence(self, user_message: str) -> float: ...
    @abstractmethod
    def crystallize_pattern(self, experiences: list[Experience]) -> Skill | None: ...
    @abstractmethod
    def generate_evolution_text(self, skills: list[Skill]) -> str: ...
