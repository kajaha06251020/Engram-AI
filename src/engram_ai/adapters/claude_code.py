import re
from pathlib import Path
from engram_ai.adapters.base import BaseAdapter
from engram_ai.exceptions import EvolutionError

START_DELIMITER = "<!-- engram-ai:start -->"
END_DELIMITER = "<!-- engram-ai:end -->"

class ClaudeCodeAdapter(BaseAdapter):
    """Adapter for Claude Code CLAUDE.md integration."""
    def write_skills(self, config_path: str, skills_text: str) -> None:
        path = Path(config_path)
        section = self._build_section(skills_text)
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if START_DELIMITER in content and END_DELIMITER in content:
                pattern = re.compile(re.escape(START_DELIMITER) + r".*?" + re.escape(END_DELIMITER), re.DOTALL)
                content = pattern.sub(section, content)
            else:
                content = content.rstrip() + "\n\n" + section + "\n"
        else:
            content = section + "\n"
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as e:
            raise EvolutionError(f"Failed to write to {config_path}: {e}") from e

    def read_config(self, config_path: str) -> str:
        path = Path(config_path)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _build_section(self, skills_text: str) -> str:
        from datetime import datetime
        now = datetime.now().isoformat(timespec="seconds")
        return (f"{START_DELIMITER}\n"
                f"## Engram-AI: Learned Skills\n"
                f"<!-- Auto-generated. Last evolved: {now} -->\n"
                f"{skills_text.rstrip()}\n"
                f"{END_DELIMITER}")
