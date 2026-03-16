import logging
from pathlib import Path
from typing import Callable

from engram_ai.adapters.base import BaseAdapter
from engram_ai.adapters.claude_code import ClaudeCodeAdapter
from engram_ai.core.crystallizer import Crystallizer
from engram_ai.core.evolver import Evolver
from engram_ai.core.querier import Querier, QueryResult
from engram_ai.core.recorder import Recorder
from engram_ai.events.bus import EventBus
from engram_ai.llm.base import BaseLLM
from engram_ai.llm.claude import ClaudeLLM
from engram_ai.models.evolution import EvolutionRecord
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill
from engram_ai.storage.base import BaseStorage
from engram_ai.storage.chromadb import ChromaDBStorage

logger = logging.getLogger(__name__)

DEFAULT_DATA_PATH = Path.home() / ".engram-ai" / "data"


class Forge:
    """Main entry point for Engram-AI. Experience-driven memory for AI agents."""

    def __init__(
        self,
        anthropic_api_key: str | None = None,
        storage_path: str | None = None,
        llm: BaseLLM | None = None,
        storage: BaseStorage | None = None,
        adapter: BaseAdapter | None = None,
    ) -> None:
        self._event_bus = EventBus()

        storage_dir = storage_path or str(DEFAULT_DATA_PATH)
        self._storage = storage or ChromaDBStorage(persist_path=storage_dir)
        self._llm = llm or ClaudeLLM(api_key=anthropic_api_key)
        self._adapter = adapter or ClaudeCodeAdapter()

        pending_path = str(Path(storage_dir).parent / "pending.jsonl")
        self._recorder = Recorder(
            storage=self._storage,
            event_bus=self._event_bus,
            pending_path=pending_path,
            llm=self._llm,
        )
        self._querier = Querier(storage=self._storage)
        self._crystallizer = Crystallizer(
            storage=self._storage,
            event_bus=self._event_bus,
            llm=self._llm,
        )
        self._evolver = Evolver(
            storage=self._storage,
            event_bus=self._event_bus,
            llm=self._llm,
            adapter=self._adapter,
        )

    def record(
        self,
        action: str,
        context: str,
        outcome: str,
        valence: float,
        metadata: dict | None = None,
    ) -> Experience:
        return self._recorder.record(action, context, outcome, valence, metadata)

    def record_pending(
        self,
        action: str,
        context: str,
        metadata: dict | None = None,
    ) -> None:
        self._recorder.record_pending(action, context, metadata)

    def complete_pending(self, outcome: str, valence: float) -> None:
        self._recorder.complete_pending(outcome, valence)

    def query(self, context: str, k: int = 5) -> QueryResult:
        return self._querier.query(context, k=k)

    def crystallize(
        self,
        min_experiences: int = 3,
        min_confidence: float = 0.7,
    ) -> list[Skill]:
        return self._crystallizer.crystallize(min_experiences, min_confidence)

    def evolve(self, config_path: str = "./CLAUDE.md") -> EvolutionRecord | None:
        return self._evolver.evolve(config_path)

    def status(self) -> dict:
        experiences = self._storage.get_all_experiences()
        skills = self._storage.get_all_skills()
        unapplied = self._storage.get_unapplied_skills()
        return {
            "total_experiences": len(experiences),
            "total_skills": len(skills),
            "unapplied_skills": len(unapplied),
        }

    def detect_valence(self, message: str) -> float:
        """Detect valence from user message using tiered strategy."""
        return self._recorder.detect_valence(message)

    def on(self, event_name: str, callback: Callable) -> None:
        self._event_bus.on(event_name, callback)
