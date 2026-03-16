import logging
from engram_ai.events.bus import EventBus
from engram_ai.events.events import SKILL_CRYSTALLIZED
from engram_ai.llm.base import BaseLLM
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill
from engram_ai.storage.base import BaseStorage

logger = logging.getLogger(__name__)
SIMILARITY_THRESHOLD = 0.4

class Crystallizer:
    """Extracts skill patterns from accumulated experiences."""
    def __init__(self, storage: BaseStorage, event_bus: EventBus, llm: BaseLLM) -> None:
        self._storage = storage
        self._event_bus = event_bus
        self._llm = llm

    def crystallize(self, min_experiences: int = 3, min_confidence: float = 0.7) -> list[Skill]:
        all_experiences = self._storage.get_all_experiences()
        if len(all_experiences) < min_experiences:
            return []
        clusters = self._cluster_experiences(all_experiences, min_experiences)
        skills = []
        for cluster in clusters:
            skill = self._llm.crystallize_pattern(cluster)
            if skill is not None and skill.confidence >= min_confidence:
                self._storage.store_skill(skill)
                self._event_bus.emit(SKILL_CRYSTALLIZED, skill)
                skills.append(skill)
        return skills

    def _cluster_experiences(self, experiences: list[Experience], min_size: int) -> list[list[Experience]]:
        visited: set[str] = set()
        clusters: list[list[Experience]] = []
        for exp in experiences:
            if exp.id in visited:
                continue
            visited.add(exp.id)
            similar = self._storage.query_experiences(exp.context, k=20)
            cluster = [exp]
            for similar_exp, similarity in similar:
                if similar_exp.id != exp.id and similarity >= SIMILARITY_THRESHOLD and similar_exp.id not in visited:
                    cluster.append(similar_exp)
                    visited.add(similar_exp.id)
            if len(cluster) >= min_size:
                clusters.append(cluster)
        return clusters
