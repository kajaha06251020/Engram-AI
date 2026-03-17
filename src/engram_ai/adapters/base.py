from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """Abstract adapter for writing learned skills to agent config."""
    @abstractmethod
    def write_skills(self, config_path: str, skills_text: str) -> None: ...
    @abstractmethod
    def read_config(self, config_path: str) -> str: ...

    # v0.2: concrete default for backward compatibility
    def write_anti_skills(self, config_path: str, anti_skills_text: str) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} does not support write_anti_skills. "
            "Upgrade your adapter to v0.2 to use anti-skill features."
        )
