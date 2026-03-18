"""
04_no_api_key.py — Full workflow without an Anthropic API key

Requires only:  pip install engram-forge
(No anthropic package needed)

Valence detection falls back to keyword matching.
Crystallization falls back to keyword-frequency clustering.
"""
from engram_ai.llm.base import BaseLLM
from engram_ai import Forge


class KeywordOnlyLLM(BaseLLM):
    """Minimal stub that disables LLM-powered features.

    The recorder and crystallizer automatically fall back to keyword-based
    algorithms when this LLM raises NotImplementedError.
    """
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("No LLM configured")

    def extract_experience(self, messages: list) -> dict | None:
        return None  # observe() will be disabled


forge = Forge(llm=KeywordOnlyLLM(), storage_path="/tmp/engram-nokey")

# ── Keyword-based valence detection ──────────────────────────────────────────
# These phrases trigger the built-in keyword detector:
experiences = [
    ("Used type hints throughout the module",  "Writing new service class",   "Great, approves", 0.0),
    ("Skipped type hints in public methods",   "Writing new service class",   "Rejected: add types", 0.0),
    ("Added docstrings to all public methods", "Code review preparation",     "Approved, nice", 0.0),
    ("Left methods undocumented",              "Code review preparation",     "Bad: needs docs", 0.0),
]

print("Recording experiences (valence will be keyword-detected)...")
for action, context, outcome, _ in experiences:
    # Pass valence=0 — the recorder will detect it from the outcome text
    exp = forge.record(action=action, context=context, outcome=outcome, valence=0.0)
    print(f"  [{exp.valence:+.1f}] {action[:50]}")

# ── Keyword-based crystallization ────────────────────────────────────────────
print("\nCrystallizing (keyword clustering, no LLM)...")
skills = forge.crystallize(min_experiences=1, min_confidence=0.3)
if skills:
    for s in skills:
        print(f"  [{s.confidence:.2f}] {s.rule}")
else:
    print("  No clusters formed yet — record more experiences.")

# ── Query still works perfectly ───────────────────────────────────────────────
print("\nQuerying: 'code documentation'")
result = forge.query("code documentation and type hints")
for exp, score in result["best"]:
    print(f"  DO    [{score:.2f}] {exp.action}")
for exp, score in result["avoid"]:
    print(f"  AVOID [{score:.2f}] {exp.action}")

print("\nStatus:", forge.status())
