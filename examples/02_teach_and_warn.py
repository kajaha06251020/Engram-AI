"""
02_teach_and_warn.py — Teach rules directly, check warnings before acting

Run:
    pip install engram-forge
    python examples/02_teach_and_warn.py
"""
from engram_ai import Forge

forge = Forge(storage_path="/tmp/engram-02")

# ── Teach rules directly (no LLM needed) ─────────────────────────────────────
print("Teaching rules...")

forge.teach(
    rule="Always validate user input at the API boundary before processing",
    context_pattern="handling HTTP requests or user input",
    skill_type="positive",
    confidence=0.95,
)

forge.teach(
    rule="Never run DELETE queries without a WHERE clause in production",
    context_pattern="database operations",
    skill_type="anti",
    confidence=1.0,
)

forge.teach(
    rule="Never use eval() or exec() on user-supplied strings",
    context_pattern="executing dynamic code",
    skill_type="anti",
    confidence=1.0,
)

# ── Seed some past failures ───────────────────────────────────────────────────
print("Recording past failures...")

forge.record(
    action="Ran DELETE FROM orders without WHERE clause",
    context="Database cleanup script in production",
    outcome="Wiped entire orders table — 3-hour restore from backup",
    valence=-1.0,
)
forge.record(
    action="Executed raw SQL query string from URL parameter",
    context="Search endpoint implementation",
    outcome="SQL injection vulnerability — flagged in security review",
    valence=-0.95,
)

# ── Warn before a new risky action ────────────────────────────────────────────
actions_to_check = [
    ("Delete all records older than 30 days", "Database maintenance script"),
    ("Add caching layer to user profile endpoint", "Performance optimization"),
    ("Parse SQL query from request body", "Advanced search feature"),
]

print("\nChecking for warnings before acting:")
for action, context in actions_to_check:
    warnings = forge.warn(action=action, context=context, threshold=0.4)
    if warnings:
        print(f"\n  ACTION: {action}")
        print(f"  WARNING — {len(warnings)} past issue(s):")
        for w in warnings:
            print(f"    [{w.valence:.1f}] {w.outcome}")
    else:
        print(f"\n  ACTION: {action}  → No warnings, safe to proceed.")
