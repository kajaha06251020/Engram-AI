"""
06_custom_llm.py — Plug in any LLM by implementing BaseLLM

This example shows how to use OpenAI (or any other provider) instead of
Anthropic. The BaseLLM interface has two methods to implement:
  - generate(prompt) → str
  - extract_experience(messages) → dict | None

Requires:  pip install "engram-forge" openai
           export OPENAI_API_KEY=sk-...
"""
import json
import os
from engram_ai.llm.base import BaseLLM
from engram_ai import Forge


class OpenAILLM(BaseLLM):
    """Engram-AI LLM adapter for OpenAI."""

    def __init__(self, model: str = "gpt-4o-mini"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run: pip install openai")
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._model = model

    def generate(self, prompt: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        return resp.choices[0].message.content or ""

    def extract_experience(self, messages: list[dict]) -> dict | None:
        """Extract action/context/outcome/valence from a message list."""
        transcript = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )
        prompt = f"""
Analyze this conversation and extract a single learning experience.
Return ONLY valid JSON in this exact format:
{{
  "action": "what the AI agent did",
  "context": "the situation or task",
  "outcome": "what happened as a result",
  "valence": <float between -1.0 and 1.0>
}}
valence: 1.0 = very positive, -1.0 = very negative, 0.0 = neutral.
If no clear experience is present, return null.

CONVERSATION:
{transcript}
""".strip()

        raw = self.generate(prompt).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None

        if not isinstance(data, dict):
            return None
        required = {"action", "context", "outcome", "valence"}
        if not required.issubset(data):
            return None
        return data


# ── Usage ─────────────────────────────────────────────────────────────────────
if not os.getenv("OPENAI_API_KEY"):
    print("Set OPENAI_API_KEY to run this example.")
    raise SystemExit(1)

forge = Forge(llm=OpenAILLM(), storage_path="/tmp/engram-openai")

forge.record(
    action="Used async/await for database calls",
    context="Refactoring synchronous endpoint to async",
    outcome="Response time dropped from 800ms to 120ms",
    valence=0.9,
)

print("Query: async patterns")
result = forge.query("async database patterns")
for exp, score in result["best"]:
    print(f"  [{score:.2f}] {exp.action}")

print("Done.")
