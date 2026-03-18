"""
05_observe.py — Auto-record experiences from a conversation

Requires:  pip install "engram-forge[claude]"
           export ANTHROPIC_API_KEY=sk-...

observe() extracts action/context/outcome/valence from a message list
using the LLM. Useful for building wrappers around AI chat interfaces.
"""
import os
from engram_ai import Forge

if not os.getenv("ANTHROPIC_API_KEY"):
    print("Set ANTHROPIC_API_KEY to run this example.")
    raise SystemExit(1)

forge = Forge(storage_path="/tmp/engram-observe")

# ── Simulate conversation snippets ────────────────────────────────────────────
conversations = [
    [
        {"role": "user",      "content": "Can you refactor this function to use a generator instead of building a list?"},
        {"role": "assistant", "content": "Sure — here's the generator version using `yield`..."},
        {"role": "user",      "content": "Perfect, much cleaner. Thanks!"},
    ],
    [
        {"role": "user",      "content": "Please add error handling to this file upload function."},
        {"role": "assistant", "content": "I've added try/except blocks and validation for file size and type..."},
        {"role": "user",      "content": "Good, but you missed the case where the directory doesn't exist."},
    ],
    [
        {"role": "user",      "content": "Write unit tests for the payment service."},
        {"role": "assistant", "content": "Here are the tests using pytest with mocked Stripe calls..."},
        {"role": "user",      "content": "Great coverage! Ship it."},
    ],
]

print("Observing conversations...")
total_recorded = 0
total_crystallized = 0

for i, messages in enumerate(conversations, 1):
    result = forge.observe(
        messages=messages,
        max_turns=3,
        crystallize_threshold=3,   # crystallize every 3 experiences
    )

    exp = result["recorded"]
    if exp:
        total_recorded += 1
        print(f"\n  Conv {i}: Recorded")
        print(f"    Action:  {exp.action}")
        print(f"    Valence: {exp.valence:+.2f}")

    if result["crystallized"]:
        total_crystallized += len(result["crystallized"])
        print(f"    → {len(result['crystallized'])} skill(s) crystallized")

print(f"\nTotal: {total_recorded} experiences, {total_crystallized} skills crystallized")
print("Status:", forge.status())
