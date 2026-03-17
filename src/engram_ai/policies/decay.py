import logging
import math
from datetime import datetime

from pydantic import BaseModel

from engram_ai.events.events import EXPERIENCE_RECORDED, SKILL_DECAYED
from engram_ai.models.skill import Skill

logger = logging.getLogger(__name__)


class DecayConfig(BaseModel):
    half_life_days: float = 90.0
    min_confidence: float = 0.1
    event_penalty: float = 0.15
    event_valence_threshold: float = -0.3
    event_similarity_threshold: float = 0.3


class DecayPolicy:
    """Confidence decay via time-based and event-based mechanisms."""

    def __init__(self, storage, event_bus, config=None):
        self._storage = storage
        self._event_bus = event_bus
        self._config = config or DecayConfig()
        event_bus.on(EXPERIENCE_RECORDED, self._on_experience_recorded)

    def apply_time_decay(self) -> list[Skill]:
        """Apply time-based decay to all active skills. Returns updated skills."""
        skills = self._storage.get_all_skills()
        updated = []
        now = datetime.now()
        for skill in skills:
            ref_date = skill.last_reinforced_at or skill.created_at
            days_elapsed = (now - ref_date).total_seconds() / 86400
            if days_elapsed <= 0:
                continue
            factor = math.pow(0.5, days_elapsed / self._config.half_life_days)
            new_conf = skill.confidence * factor
            new_conf = max(0.0, new_conf)
            skill.confidence = round(new_conf, 4)
            self._storage.update_skill(skill)
            updated.append(skill)
            if skill.confidence < self._config.min_confidence:
                self._event_bus.emit(SKILL_DECAYED, skill)
        return updated

    def _on_experience_recorded(self, experience):
        """Event decay: negative experiences reduce confidence of related skills."""
        if experience.valence >= self._config.event_valence_threshold:
            return
        similar_skills = self._storage.query_skills(experience.context)
        for skill, similarity in similar_skills:
            if similarity < self._config.event_similarity_threshold:
                continue
            direction = skill.valence_summary.get("positive", 0) - skill.valence_summary.get("negative", 0)
            # Experience is negative (< threshold), skill is positive (direction > 0) -> opposite
            if direction > 0 and experience.valence < 0:
                skill.confidence = max(0.0, skill.confidence - self._config.event_penalty)
                self._storage.update_skill(skill)
                if skill.confidence < self._config.min_confidence:
                    self._event_bus.emit(SKILL_DECAYED, skill)
