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

    # v0.2: concrete defaults for backward compatibility
    def verify_conflict(self, skill_a: Skill, skill_b: Skill) -> bool:
        raise NotImplementedError(
            f"{type(self).__name__} does not support verify_conflict. "
            "Upgrade your LLM implementation to v0.2."
        )

    def merge_skills(self, skill_a: Skill, skill_b: Skill) -> Skill:
        raise NotImplementedError(
            f"{type(self).__name__} does not support merge_skills. "
            "Upgrade your LLM implementation to v0.2."
        )
