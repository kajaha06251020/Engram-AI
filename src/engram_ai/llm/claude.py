import json
import logging
try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

from engram_ai.exceptions import LLMError
from engram_ai.llm.base import BaseLLM
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill

logger = logging.getLogger(__name__)

class ClaudeLLM(BaseLLM):
    """Claude API implementation for Engram-AI LLM operations."""
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        if anthropic is None:
            raise ImportError(
                "anthropic package is required for ClaudeLLM. "
                "Install it with: pip install engram-ai[claude]"
            )
        try:
            self._client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            raise LLMError(f"Failed to initialize Anthropic client: {e}") from e
        self._model = model

    def _call(self, system: str, user: str) -> str:
        try:
            response = self._client.messages.create(
                model=self._model, max_tokens=1024, system=system,
                messages=[{"role": "user", "content": user}])
            return response.content[0].text
        except Exception as e:
            raise LLMError(f"Claude API call failed: {e}") from e

    def detect_valence(self, user_message: str) -> float:
        system = ("You are a sentiment analyzer. Given a user message that is a response "
                  "to an AI assistant's action, rate the sentiment from -1.0 (very negative) "
                  "to +1.0 (very positive). Respond with ONLY a single float number.")
        result = self._call(system, user_message)
        try:
            valence = float(result.strip())
            return max(-1.0, min(1.0, valence))
        except ValueError:
            logger.warning("Failed to parse valence from: %s", result)
            return 0.0

    def crystallize_pattern(self, experiences: list[Experience]) -> Skill | None:
        system = ("You analyze AI agent experiences and extract reusable rules. "
                  "Given a cluster of related experiences (action, context, outcome, valence), "
                  "identify the pattern and create a skill rule.\n"
                  'Respond with JSON: {"rule": "...", "context_pattern": "...", "confidence": 0.0-1.0}\n'
                  'If no clear pattern exists, respond with: {"rule": null}')
        exp_data = [{"action": e.action, "context": e.context, "outcome": e.outcome, "valence": e.valence} for e in experiences]
        result = self._call(system, json.dumps(exp_data, ensure_ascii=False))
        try:
            parsed = json.loads(result)
            if parsed.get("rule") is None:
                return None
            positive = sum(1 for e in experiences if e.valence > 0)
            negative = sum(1 for e in experiences if e.valence < 0)
            return Skill(
                rule=parsed["rule"], context_pattern=parsed.get("context_pattern", ""),
                confidence=parsed.get("confidence", 0.5),
                source_experiences=[e.id for e in experiences], evidence_count=len(experiences),
                valence_summary={"positive": positive, "negative": negative})
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse crystallize response: %s", e)
            return None

    def generate_evolution_text(self, skills: list[Skill]) -> str:
        system = ("Generate a concise markdown list of learned skills for an AI agent's "
                  "configuration file. Each skill should be one line with its confidence score. "
                  "Output ONLY the markdown list, no headers or extra text.")
        skills_data = [{"rule": s.rule, "confidence": s.confidence} for s in skills]
        return self._call(system, json.dumps(skills_data, ensure_ascii=False))

    def verify_conflict(self, skill_a: Skill, skill_b: Skill) -> bool:
        system = (
            "You determine if two AI agent skills contradict each other. "
            "Respond with ONLY 'true' or 'false'."
        )
        user = (
            f"Skill A: {skill_a.rule} (context: {skill_a.context_pattern})\n"
            f"Skill B: {skill_b.rule} (context: {skill_b.context_pattern})\n"
            "Do these skills contradict each other?"
        )
        result = self._call(system, user)
        return result.strip().lower() == "true"

    def merge_skills(self, skill_a: Skill, skill_b: Skill) -> Skill:
        system = (
            "You merge two contradicting AI agent skills into one unified skill. "
            'Respond with JSON: {"rule": "...", "context_pattern": "...", "confidence": 0.0-1.0}'
        )
        user = (
            f"Skill A: {skill_a.rule} (confidence: {skill_a.confidence})\n"
            f"Skill B: {skill_b.rule} (confidence: {skill_b.confidence})\n"
            "Create a merged skill that resolves the contradiction."
        )
        result = self._call(system, user)
        parsed = json.loads(result)
        combined_sources = list(set(skill_a.source_experiences + skill_b.source_experiences))
        pos = skill_a.valence_summary.get("positive", 0) + skill_b.valence_summary.get("positive", 0)
        neg = skill_a.valence_summary.get("negative", 0) + skill_b.valence_summary.get("negative", 0)
        return Skill(
            rule=parsed["rule"],
            context_pattern=parsed.get("context_pattern", ""),
            confidence=parsed.get("confidence", max(skill_a.confidence, skill_b.confidence)),
            source_experiences=combined_sources,
            evidence_count=skill_a.evidence_count + skill_b.evidence_count,
            valence_summary={"positive": pos, "negative": neg},
        )

    def extract_experience(self, messages: list[dict]) -> dict | None:
        system = (
            "You analyze conversations between a user and an AI assistant to extract "
            "notable experiences worth recording for future learning.\n\n"
            "Look for: technical learnings, failure lessons, success patterns, "
            "debugging insights, or important caveats.\n"
            "Skip: casual chat, greetings, pure questions without resolution, "
            "trivial exchanges.\n\n"
            "If the conversation contains a recordable experience, respond with ONLY "
            "a JSON object:\n"
            '{"action": "<what was done>", "context": "<situation/problem>", '
            '"outcome": "<what happened/result>", "valence": <float from -1.0 to 1.0>}\n\n'
            "If there is no notable experience, respond with ONLY:\n"
            '{"experience": null}'
        )
        transcript = "\n".join(
            f"[{m['role']}]: {m['content']}" for m in messages
        )
        result = self._call(system, transcript)
        try:
            parsed = json.loads(result)
            if parsed.get("experience") is None and "action" not in parsed:
                return None
            required = ("action", "context", "outcome", "valence")
            if not all(k in parsed for k in required):
                return None
            parsed["valence"] = max(-1.0, min(1.0, float(parsed["valence"])))
            return {k: parsed[k] for k in required}
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning("Failed to parse extract_experience response: %s", e)
            return None
