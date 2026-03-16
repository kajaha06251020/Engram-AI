from abc import ABC, abstractmethod
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill

class BaseStorage(ABC):
    """Abstract storage interface for experiences and skills."""

    @abstractmethod
    def store_experience(self, experience: Experience) -> str: ...

    @abstractmethod
    def query_experiences(self, context: str, k: int = 5) -> list[tuple[Experience, float]]: ...

    @abstractmethod
    def get_all_experiences(self) -> list[Experience]: ...

    @abstractmethod
    def store_skill(self, skill: Skill) -> str: ...

    @abstractmethod
    def get_all_skills(self) -> list[Skill]: ...

    @abstractmethod
    def get_unapplied_skills(self) -> list[Skill]: ...

    @abstractmethod
    def mark_skills_applied(self, skill_ids: list[str]) -> None: ...
