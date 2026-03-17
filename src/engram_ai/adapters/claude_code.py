from pathlib import Path
from engram_ai.adapters.base import BaseAdapter
from engram_ai.adapters._delimiters import write_delimited_section

START_DELIMITER = "<!-- engram-ai:start -->"
END_DELIMITER = "<!-- engram-ai:end -->"
ANTI_START = "<!-- engram-ai:anti-skills:start -->"
ANTI_END = "<!-- engram-ai:anti-skills:end -->"


class ClaudeCodeAdapter(BaseAdapter):
    """Adapter for Claude Code CLAUDE.md integration."""

    def write_skills(self, config_path: str, skills_text: str) -> None:
        write_delimited_section(
            Path(config_path), skills_text,
            START_DELIMITER, END_DELIMITER, "Engram-AI: Learned Skills",
        )

    def write_anti_skills(self, config_path: str, anti_skills_text: str) -> None:
        write_delimited_section(
            Path(config_path), anti_skills_text,
            ANTI_START, ANTI_END, "Engram-AI: Anti-Patterns (Avoid)",
        )

    def read_config(self, config_path: str) -> str:
        path = Path(config_path)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
