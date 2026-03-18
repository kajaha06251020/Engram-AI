import gc
import re
import shutil
import logging
from pathlib import Path
from engram_ai.forge import Forge
from engram_ai.llm.base import BaseLLM

logger = logging.getLogger(__name__)

_PROJECT_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class ProjectManager:
    """Factory that manages per-project Forge instances."""

    def __init__(self, base_path: Path, llm: BaseLLM | None = None, config: dict | None = None) -> None:
        self._base_path = Path(base_path)
        self._llm = llm
        self._config = config or {}
        self._default_project = self._config.get("default_project", "default")
        self._cache: dict[str, Forge] = {}

    def _validate_name(self, name: str) -> None:
        if not _PROJECT_NAME_RE.match(name):
            raise ValueError(
                f"Invalid project name '{name}': use only alphanumeric, hyphens, underscores"
            )

    def _resolve_path(self, project: str) -> Path:
        """Resolve storage path for a project, handling backward compatibility."""
        project_path = self._base_path / project
        # Backward compat: if base_path itself has chroma.sqlite3, it's old layout
        if project == self._default_project and not project_path.exists():
            old_db = self._base_path / "chroma.sqlite3"
            if old_db.exists():
                return self._base_path
        return project_path

    def get_forge(self, project: str | None = None) -> Forge:
        """Return Forge for the given project. Creates project dir if needed."""
        name = project or self._default_project
        self._validate_name(name)
        if name in self._cache:
            return self._cache[name]
        storage_path = self._resolve_path(name)
        storage_path.mkdir(parents=True, exist_ok=True)
        forge = Forge(
            storage_path=str(storage_path),
            llm=self._llm,
            enable_policies=True,
        )
        self._cache[name] = forge
        return forge

    def list_projects(self) -> list[str]:
        """List project names (subdirectories of base_path)."""
        if not self._base_path.exists():
            return []
        return sorted(
            d.name for d in self._base_path.iterdir()
            if d.is_dir() and _PROJECT_NAME_RE.match(d.name)
        )

    def delete_project(self, name: str) -> None:
        """Remove a project's data directory."""
        if name == self._default_project:
            raise ValueError(f"Cannot delete the default project '{name}'")
        self._validate_name(name)
        # Close and evict from cache first so file handles are released before rmtree
        forge = self._cache.pop(name, None)
        if forge is not None:
            forge.close()
        gc.collect()
        project_path = self._base_path / name
        if project_path.exists():
            shutil.rmtree(project_path)

    def get_all_forges(self) -> dict[str, Forge]:
        """Return Forge instances for all existing projects."""
        for name in self.list_projects():
            if name not in self._cache:
                self.get_forge(name)
        return dict(self._cache)
