import json
import logging
import anthropic
from engram_ai.exceptions import LLMError
from engram_ai.llm.base import BaseLLM
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill

logger = logging.getLogger(__name__)

class ClaudeLLM(BaseLLM):
    """Claude API implementation for Engram-AI LLM operations."""
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514"):
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
