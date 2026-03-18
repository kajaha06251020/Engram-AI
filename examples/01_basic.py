"""
01_basic.py — Record, query, crystallize, evolve

Run:
    pip install engram-forge
    python examples/01_basic.py

No Anthropic API key required (uses keyword-based fallback).
"""
from engram_ai import Forge

forge = Forge(storage_path="/tmp/engram-01")

# ── Record experiences ────────────────────────────────────────────────────────
pairs = [
    (
        "Used f-strings for log messages",
        "Adding debug logging to API server",
        "Clean output, reviewer approved it",
        0.9,
    ),
    (
        "Used % formatting for log messages",
        "Adding debug logging to API server",
        "Team said it was old-style, asked to rewrite",
        -0.6,
    ),
    (
        "Used f-strings in utility script",
        "Writing one-off data processing script",
        "Readable and fast — no comments from reviewer",
        0.7,
    ),
    (
        "Used str.format() in test assertions",
        "Writing pytest tests",
        "Reviewer flagged as verbose, suggested f-strings",
        -0.4,
    ),
]

print("Recording experiences...")
for action, context, outcome, valence in pairs:
    exp = forge.record(action=action, context=context, outcome=outcome, valence=valence)
    sign = "+" if valence >= 0 else ""
    print(f"  [{sign}{valence:.1f}] {action[:50]}")

# ── Query ─────────────────────────────────────────────────────────────────────
print("\nQuerying: 'string formatting in Python'")
result = forge.query("string formatting in Python", k=3)

if result["best"]:
    print("  DO:")
    for exp, score in result["best"]:
        print(f"    [{score:.2f}] {exp.action}")

if result["avoid"]:
    print("  AVOID:")
    for exp, score in result["avoid"]:
        print(f"    [{score:.2f}] {exp.action}")

# ── Crystallize ───────────────────────────────────────────────────────────────
print("\nCrystallizing skills...")
skills = forge.crystallize(min_experiences=2, min_confidence=0.4)
if skills:
    for skill in skills:
        print(f"  [{skill.confidence:.2f}] {skill.rule}")
else:
    print("  No skills crystallized yet (need more experiences).")

# ── Status ────────────────────────────────────────────────────────────────────
stats = forge.status()
print(f"\nStatus: {stats['total_experiences']} experiences, {stats['total_skills']} skills")

# ── Evolve ────────────────────────────────────────────────────────────────────
record = forge.evolve(config_path="/tmp/AGENT_01.md")
if record:
    print(f"\nEvolved config:\n{record.diff}")
else:
    print("\nNo unapplied skills to evolve.")
