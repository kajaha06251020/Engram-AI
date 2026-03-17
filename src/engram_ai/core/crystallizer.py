import logging
from datetime import datetime

from engram_ai.events.bus import EventBus
from engram_ai.events.events import SKILL_CRYSTALLIZED, SKILL_REINFORCED
from engram_ai.llm.base import BaseLLM
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill
from engram_ai.storage.base import BaseStorage

logger = logging.getLogger(__name__)
SIMILARITY_THRESHOLD = 0.4
REINFORCEMENT_THRESHOLD = 0.5


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
                # Check for reinforcement match
                existing_match = self._find_matching_skill(skill)
                if existing_match:
                    self._reinforce_skill(existing_match, cluster)
                    skills.append(existing_match)
                else:
                    self._storage.store_skill(skill)
                    self._event_bus.emit(SKILL_CRYSTALLIZED, skill)
                    skills.append(skill)
        return skills

    def _find_matching_skill(self, candidate: Skill) -> Skill | None:
        similar = self._storage.query_skills(candidate.rule, k=3)
        for existing, similarity in similar:
            if similarity >= REINFORCEMENT_THRESHOLD:
                return existing
        return None

    def _reinforce_skill(self, skill: Skill, cluster: list[Experience]) -> None:
        skill.confidence = min(1.0, skill.confidence + 0.1)
        skill.reinforcement_count += 1
        skill.last_reinforced_at = datetime.now()
        new_ids = [e.id for e in cluster if e.id not in skill.source_experiences]
        skill.source_experiences.extend(new_ids)
        skill.evidence_count = len(skill.source_experiences)
        self._storage.update_skill(skill)
        self._event_bus.emit(SKILL_REINFORCED, skill)

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
