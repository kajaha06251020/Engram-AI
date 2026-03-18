import logging
from pathlib import Path
from typing import Callable

from engram_ai.adapters import ADAPTER_REGISTRY
from engram_ai.adapters.base import BaseAdapter
from engram_ai.adapters.claude_code import ClaudeCodeAdapter
from engram_ai.core.crystallizer import Crystallizer
from engram_ai.core.evolver import Evolver
from engram_ai.core.querier import Querier, QueryResult
from engram_ai.core.recorder import Recorder
from engram_ai.events.bus import EventBus
from engram_ai.exceptions import EngramError
from engram_ai.llm.base import BaseLLM
from engram_ai.models.evolution import EvolutionRecord
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill
from engram_ai.policies.conflict import ConflictPolicy
from engram_ai.policies.decay import DecayConfig, DecayPolicy
from engram_ai.storage.base import BaseStorage
from engram_ai.storage.chromadb import ChromaDBStorage

logger = logging.getLogger(__name__)

DEFAULT_DATA_PATH = Path.home() / ".engram-ai" / "data"


def _trim_messages(messages: list[dict], max_turns: int = 3) -> list[dict]:
    """Trim messages to the last max_turns turn pairs.

    Strips empty content and non-user/assistant roles, then takes
    the last max_turns*2 messages.
    """
    filtered = [
        m for m in messages
        if m.get("role") in ("user", "assistant") and m.get("content", "").strip()
    ]
    limit = max_turns * 2
    if len(filtered) <= limit:
        return filtered
    return filtered[-limit:]


class Forge:
    """Main entry point for Engram-AI. Experience-driven memory for AI agents."""

    def __init__(
        self,
        anthropic_api_key: str | None = None,
        storage_path: str | None = None,
        llm: BaseLLM | None = None,
        storage: BaseStorage | None = None,
        adapter: BaseAdapter | None = None,
        decay_config: DecayConfig | None = None,
        enable_policies: bool = False,
    ) -> None:
        self._event_bus = EventBus()

        storage_dir = storage_path or str(DEFAULT_DATA_PATH)
        self._storage = storage or ChromaDBStorage(persist_path=storage_dir)
        if llm is not None:
            self._llm = llm
        elif anthropic_api_key is not None:
            from engram_ai.llm.claude import ClaudeLLM
            self._llm = ClaudeLLM(api_key=anthropic_api_key)
        else:
            # Try ClaudeLLM with env key; raise helpful error if anthropic missing
            try:
                from engram_ai.llm.claude import ClaudeLLM
                self._llm = ClaudeLLM()
            except ImportError:
                raise ImportError(
                    "No LLM provided and anthropic package is not installed. "
                    "Either pass llm= explicitly, or install: pip install engram-ai[claude]"
                )
        self._adapter = adapter or ClaudeCodeAdapter()

        pending_path = str(Path(storage_dir) / "pending.jsonl")
        self._recorder = Recorder(
            storage=self._storage, event_bus=self._event_bus,
            pending_path=pending_path, llm=self._llm,
        )
        self._querier = Querier(storage=self._storage)
        self._crystallizer = Crystallizer(
            storage=self._storage, event_bus=self._event_bus, llm=self._llm,
        )
        self._evolver = Evolver(
            storage=self._storage, event_bus=self._event_bus,
            llm=self._llm, adapter=self._adapter,
        )

        # v0.2: Policies
        if enable_policies:
            self._decay_policy = DecayPolicy(self._storage, self._event_bus, decay_config)
            self._conflict_policy = ConflictPolicy(self._storage, self._event_bus, self._llm)
        else:
            self._decay_policy = None
            self._conflict_policy = None

    @classmethod
    def with_adapter(cls, adapter_name: str = "claude-code", **kwargs) -> "Forge":
        if adapter_name not in ADAPTER_REGISTRY:
            raise EngramError(
                f"Unknown adapter: {adapter_name!r}. "
                f"Valid options: {list(ADAPTER_REGISTRY)}"
            )
        entry = ADAPTER_REGISTRY[adapter_name]
        adapter = entry["class"]()
        return cls(adapter=adapter, **kwargs)

    def record(self, action: str, context: str, outcome: str, valence: float,
               metadata: dict | None = None, parent_id: str | None = None) -> Experience:
        exp = self._recorder.record(action, context, outcome, valence, metadata, parent_id)
        self._check_skill_effectiveness(exp)
        return exp

    def record_pending(self, action: str, context: str,
                       metadata: dict | None = None, parent_id: str | None = None) -> None:
        self._recorder.record_pending(action, context, metadata, parent_id)

    def complete_pending(self, outcome: str, valence: float) -> "Experience | None":
        return self._recorder.complete_pending(outcome, valence)

    def query(self, context: str, k: int = 5) -> QueryResult:
        return self._querier.query(context, k=k)

    def crystallize(self, min_experiences: int = 3, min_confidence: float = 0.7) -> list[Skill]:
        return self._crystallizer.crystallize(min_experiences, min_confidence)

    def evolve(self, config_path: str = "./CLAUDE.md") -> EvolutionRecord | None:
        return self._evolver.evolve(config_path)

    def apply_decay(self) -> list[Skill]:
        if self._decay_policy:
            return self._decay_policy.apply_time_decay()
        return []

    def detect_conflicts(self) -> list[tuple[Skill, Skill]]:
        if self._conflict_policy:
            return self._conflict_policy.detect_all_conflicts()
        return []

    def merge_skills(self, skill_a_id: str, skill_b_id: str) -> Skill:
        if not self._conflict_policy:
            raise EngramError("Conflict policy not enabled")
        return self._conflict_policy.auto_merge(skill_a_id, skill_b_id)

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
        return self._recorder.detect_valence(message)

    def _check_skill_effectiveness(self, experience: "Experience") -> list["Skill"]:
        """Evaluate applied skills against a new experience.
        Returns skills whose confidence was adjusted."""
        from engram_ai.events.events import SKILL_EFFECTIVENESS_UPDATED

        adjusted = []
        try:
            similar_skills = self._storage.query_skills(experience.context, k=5)
        except Exception:
            return adjusted

        for skill, similarity in similar_skills:
            if similarity < 0.5:
                continue

            changed = False
            if experience.valence >= 0.3:
                skill.prediction_hits += 1
                changed = True
            elif experience.valence <= -0.3:
                skill.prediction_misses += 1
                changed = True

            if not changed:
                continue

            total = skill.prediction_hits + skill.prediction_misses
            if total >= 3:
                hit_rate = skill.prediction_hits / total
                if hit_rate <= 0.3 and skill.prediction_misses >= 3:
                    skill.confidence = round(skill.confidence * 0.7, 4)
                    adjusted.append(skill)
                elif hit_rate >= 0.8 and skill.prediction_hits >= 3:
                    skill.confidence = min(1.0, round(skill.confidence + 0.1, 4))
                    adjusted.append(skill)

            self._storage.update_skill(skill)

        for skill in adjusted:
            self._event_bus.emit(SKILL_EFFECTIVENESS_UPDATED, skill)

        return adjusted

    def observe(self, messages: list[dict], max_turns: int = 3,
                crystallize_threshold: int = 5) -> dict:
        """Observe a conversation snippet and auto-record/crystallize."""
        if crystallize_threshold < 2:
            raise EngramError("crystallize_threshold must be >= 2")

        trimmed = _trim_messages(messages, max_turns)
        if not trimmed:
            return {"recorded": None, "crystallized": []}

        try:
            extracted = self._llm.extract_experience(trimmed)
        except NotImplementedError:
            raise EngramError(
                "observe requires an LLM that supports extract_experience"
            )

        if extracted is None:
            return {"recorded": None, "crystallized": []}

        exp = self.record(
            action=extracted["action"],
            context=extracted["context"],
            outcome=extracted["outcome"],
            valence=extracted["valence"],
        )

        crystallized = []
        count = len(self._storage.get_all_experiences())
        if count >= crystallize_threshold and count % crystallize_threshold == 0:
            crystallized = self.crystallize()

        return {"recorded": exp, "crystallized": crystallized}

    def teach(self, rule: str, context_pattern: str,
              skill_type: str = "positive",
              confidence: float = 0.8) -> Skill:
        """Create a skill directly from user instruction."""
        if skill_type not in ("positive", "anti"):
            raise ValueError(f"skill_type must be 'positive' or 'anti', got {skill_type!r}")

        # Check for similar existing skill
        try:
            similar = self._storage.query_skills(rule, k=3)
            for existing_skill, sim in similar:
                if sim >= 0.5:
                    existing_skill.confidence = min(1.0, round(existing_skill.confidence + 0.1, 4))
                    existing_skill.reinforcement_count += 1
                    self._storage.update_skill(existing_skill)
                    from engram_ai.events.events import SKILL_REINFORCED
                    self._event_bus.emit(SKILL_REINFORCED, existing_skill)
                    return existing_skill
        except Exception:
            pass

        skill = Skill(
            rule=rule,
            context_pattern=context_pattern,
            confidence=confidence,
            source_experiences=[],
            evidence_count=0,
            valence_summary={},
            skill_type=skill_type,
        )
        self._storage.store_skill(skill)
        from engram_ai.events.events import SKILL_CRYSTALLIZED
        self._event_bus.emit(SKILL_CRYSTALLIZED, skill)
        return skill

    def _recall(self, context: str, k_skills: int = 3, k_experiences: int = 2) -> dict:
        """Search for relevant skills and negative experiences for a given context."""
        if not context.strip() or (k_skills == 0 and k_experiences == 0):
            return {"skills": [], "warnings": []}

        skills = []
        if k_skills > 0:
            try:
                results = self._storage.query_skills(context, k=k_skills)
                skills = [s for s, sim in results if sim >= 0.4][:k_skills]
            except Exception:
                pass

        warnings = []
        if k_experiences > 0:
            try:
                results = self._storage.query_experiences(context, k=k_experiences * 3)
                warnings = [
                    exp for exp, sim in results
                    if exp.valence < -0.3 and sim >= 0.4
                ][:k_experiences]
            except Exception:
                pass

        return {"skills": skills, "warnings": warnings}

    def warn(self, action: str, context: str, threshold: float = 0.6) -> list:
        """Search for past negative experiences similar to the current action."""
        search_text = f"{action} {context}"
        try:
            results = self._storage.query_experiences(search_text, k=10)
        except Exception:
            return []

        warnings = [
            (exp, sim) for exp, sim in results
            if exp.valence < -0.3 and sim >= threshold
        ]
        warnings.sort(key=lambda pair: pair[1], reverse=True)
        return [exp for exp, sim in warnings]

    def on(self, event_name: str, callback: Callable) -> None:
        self._event_bus.on(event_name, callback)

    def close(self) -> None:
        """Release storage resources (e.g. SQLite file handles)."""
        self._storage.close()
