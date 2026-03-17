import logging

from engram_ai.events.events import SKILL_CRYSTALLIZED, SKILL_CONFLICT_DETECTED
from engram_ai.models.skill import Skill

logger = logging.getLogger(__name__)


class ConflictPolicy:
    """Detects and resolves skill conflicts."""

    def __init__(self, storage, event_bus, llm):
        self._storage = storage
        self._event_bus = event_bus
        self._llm = llm
        event_bus.on(SKILL_CRYSTALLIZED, self._on_skill_crystallized)

    @staticmethod
    def _valence_direction(skill: Skill) -> int:
        pos = skill.valence_summary.get("positive", 0)
        neg = skill.valence_summary.get("negative", 0)
        return pos - neg

    def _on_skill_crystallized(self, new_skill: Skill):
        similar = self._storage.query_skills(new_skill.rule, k=10)
        new_dir = self._valence_direction(new_skill)
        for candidate, similarity in similar:
            if candidate.id == new_skill.id or similarity < 0.3:
                continue
            cand_dir = self._valence_direction(candidate)
            # Opposing directions: one positive, one negative
            if (new_dir > 0 and cand_dir < 0) or (new_dir < 0 and cand_dir > 0):
                if self._llm.verify_conflict(new_skill, candidate):
                    new_skill.conflicts_with.append(candidate.id)
                    candidate.conflicts_with.append(new_skill.id)
                    self._storage.update_skill(new_skill)
                    self._storage.update_skill(candidate)
                    self._event_bus.emit(SKILL_CONFLICT_DETECTED, {
                        "skill_a": new_skill,
                        "skill_b": candidate,
                    })

    def detect_all_conflicts(self) -> list[tuple[Skill, Skill]]:
        """Semantic pre-filter only (no LLM). Returns candidate conflict pairs."""
        all_skills = self._storage.get_all_skills()
        seen = set()
        conflicts = []
        for skill in all_skills:
            similar = self._storage.query_skills(skill.rule, k=10)
            skill_dir = self._valence_direction(skill)
            for candidate, similarity in similar:
                if candidate.id == skill.id or similarity < 0.3:
                    continue
                pair = tuple(sorted([skill.id, candidate.id]))
                if pair in seen:
                    continue
                seen.add(pair)
                cand_dir = self._valence_direction(candidate)
                if (skill_dir > 0 and cand_dir < 0) or (skill_dir < 0 and cand_dir > 0):
                    conflicts.append((skill, candidate))
        return conflicts

    def auto_merge(self, skill_a_id: str, skill_b_id: str) -> Skill:
        all_skills = self._storage.get_all_skills()
        skill_a = next(s for s in all_skills if s.id == skill_a_id)
        skill_b = next(s for s in all_skills if s.id == skill_b_id)
        merged = self._llm.merge_skills(skill_a, skill_b)
        self._storage.store_skill(merged)
        skill_a.status = "superseded"
        skill_b.status = "superseded"
        self._storage.update_skill(skill_a)
        self._storage.update_skill(skill_b)
        return merged
