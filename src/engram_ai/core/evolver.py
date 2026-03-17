import logging
from engram_ai.adapters.base import BaseAdapter
from engram_ai.events.bus import EventBus
from engram_ai.events.events import AGENT_EVOLVED
from engram_ai.llm.base import BaseLLM
from engram_ai.models.evolution import EvolutionRecord
from engram_ai.storage.base import BaseStorage

logger = logging.getLogger(__name__)


class Evolver:
    """Evolves agent configuration by writing learned skills."""
    def __init__(self, storage: BaseStorage, event_bus: EventBus, llm: BaseLLM, adapter: BaseAdapter) -> None:
        self._storage = storage
        self._event_bus = event_bus
        self._llm = llm
        self._adapter = adapter

    def evolve(self, config_path: str) -> EvolutionRecord | None:
        unapplied = self._storage.get_unapplied_skills()
        if not unapplied:
            logger.info("No unapplied skills to evolve")
            return None

        positive = [s for s in unapplied if s.skill_type == "positive"]
        anti = [s for s in unapplied if s.skill_type == "anti"]

        if positive:
            skills_text = self._llm.generate_evolution_text(positive)
            self._adapter.write_skills(config_path, skills_text)
        if anti:
            anti_text = self._llm.generate_evolution_text(anti)
            self._adapter.write_anti_skills(config_path, anti_text)

        skill_ids = [s.id for s in unapplied]
        self._storage.mark_skills_applied(skill_ids)
        record = EvolutionRecord(
            skills_applied=skill_ids,
            config_path=config_path,
            diff=f"+ {len(positive)} skills, + {len(anti)} anti-skills added",
        )
        self._event_bus.emit(AGENT_EVOLVED, record)
        return record
