from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """Abstract adapter for writing learned skills to agent config."""
    @abstractmethod
    def write_skills(self, config_path: str, skills_text: str) -> None: ...
    @abstractmethod
    def read_config(self, config_path: str) -> str: ...
