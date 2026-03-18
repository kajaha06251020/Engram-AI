"""
03_multi_project.py — Isolated memory per project with ProjectManager

Run:
    pip install engram-forge
    python examples/03_multi_project.py
"""
from pathlib import Path
from engram_ai import ProjectManager

pm = ProjectManager(base_path=Path("/tmp/engram-projects"))

# ── Each project gets its own isolated Forge ──────────────────────────────────
frontend = pm.get_forge("myapp/frontend")
backend  = pm.get_forge("myapp/backend")
infra    = pm.get_forge("myapp/infra")

print("Recording frontend experiences...")
frontend.record(
    action="Used Tailwind utility classes for responsive grid",
    context="Building dashboard layout component",
    outcome="Fast iteration, pixel-perfect match with design",
    valence=0.9,
)
frontend.record(
    action="Wrote custom CSS media queries for responsiveness",
    context="Building dashboard layout component",
    outcome="Took 3x longer than Tailwind, hard to maintain",
    valence=-0.5,
)

print("Recording backend experiences...")
backend.record(
    action="Used SQLAlchemy ORM for 5-table join query",
    context="Dashboard analytics endpoint",
    outcome="N+1 query problem — 2s response time, rewrote with raw SQL",
    valence=-0.7,
)
backend.record(
    action="Used raw SQL with parameterized queries for analytics",
    context="Dashboard analytics endpoint",
    outcome="50ms response, passes security review",
    valence=0.85,
)

print("Recording infra experiences...")
infra.record(
    action="Deployed with rolling update strategy",
    context="Kubernetes production deployment",
    outcome="Zero downtime, health checks passed",
    valence=0.9,
)

# ── Projects are completely isolated ─────────────────────────────────────────
print(f"\nAll projects: {pm.list_projects()}")

print("\n--- Frontend query: CSS/layout ---")
result = frontend.query("CSS layout approach")
for exp, score in result["best"]:
    print(f"  DO    [{score:.2f}] {exp.action}")
for exp, score in result["avoid"]:
    print(f"  AVOID [{score:.2f}] {exp.action}")

print("\n--- Backend query: database queries ---")
result = backend.query("database query performance")
for exp, score in result["best"]:
    print(f"  DO    [{score:.2f}] {exp.action}")
for exp, score in result["avoid"]:
    print(f"  AVOID [{score:.2f}] {exp.action}")

# ── Crystallize per project ───────────────────────────────────────────────────
print("\n--- Crystallizing backend skills ---")
skills = backend.crystallize(min_experiences=1, min_confidence=0.4)
for s in skills:
    print(f"  [{s.confidence:.2f}] {s.rule}")
