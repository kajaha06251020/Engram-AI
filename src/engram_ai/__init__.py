"""Engram-AI: Experience-driven memory infrastructure for AI agents."""

__version__ = "0.4.0"

from engram_ai.forge import Forge
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill
from engram_ai.project import ProjectManager
from engram_ai.core.querier import QueryResult

__all__ = ["Forge", "Experience", "Skill", "ProjectManager", "QueryResult"]
