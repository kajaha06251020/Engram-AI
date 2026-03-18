# Reddit — r/Python

## Title
```
engram-forge: experiential memory for AI agents — record what your agent did, query what worked, crystallize it into reusable skills
```

## Body
```
**GitHub:** https://github.com/kajaha06251020/Engram-AI
**PyPI:** https://pypi.org/project/engram-forge/

---

### What it does

Engram-AI gives AI agents memory that captures *causality*, not just facts.

Instead of storing "user prefers list comprehensions", it stores:

```python
Experience(
    action  = "Used list comprehension for 10k-row CSV transform",
    context = "Data processing pipeline",
    outcome = "Fast and readable — user approved",
    valence = 0.9,
)
```

Then it **crystallizes** patterns from accumulated experiences:

```python
forge.crystallize()
# → Skill("Prefer list comprehensions for data transforms", confidence=0.87)
```

And **evolves** them into agent config files (CLAUDE.md, AGENTS.md, etc.):

```python
forge.evolve("./CLAUDE.md")
# Writes a <!-- engram-forge:start --> block with learned rules
```

---

### Install

```bash
pip install engram-forge                    # core, no API key needed
pip install "engram-forge[claude]"          # + Anthropic LLM
pip install "engram-forge[mcp]"             # + MCP server for Claude Code
pip install "engram-forge[full]"            # everything
```

---

### Quick example

```python
from engram_ai import Forge

forge = Forge(storage_path="./agent-memory")

# Record experiences
forge.record(
    action="Used f-strings for formatting",
    context="Writing Python utility script",
    outcome="Reviewer approved — clean and readable",
    valence=0.9,
)
forge.record(
    action="Used % formatting",
    context="Writing Python utility script",
    outcome="Reviewer asked to rewrite with f-strings",
    valence=-0.6,
)

# Query — returns partitioned results
result = forge.query("string formatting in Python")
print(result["best"])   # → positive experiences
print(result["avoid"])  # → negative experiences

# Teach a rule directly (no experiences needed)
forge.teach(
    rule="Always use parameterized queries for SQL",
    context_pattern="database operations",
    skill_type="anti",
    confidence=1.0,
)

# Warn before a risky action
warnings = forge.warn("Run DELETE query", "database maintenance")

# Crystallize patterns → reusable skills
skills = forge.crystallize(min_experiences=3, min_confidence=0.7)

# Write to agent config
forge.evolve("./CLAUDE.md")
```

---

### Multi-project support

```python
from engram_ai import ProjectManager
from pathlib import Path

pm = ProjectManager(base_path=Path("~/.engram-ai/data"))
frontend = pm.get_forge("myapp/frontend")
backend  = pm.get_forge("myapp/backend")
```

---

### Extension points

```python
from engram_ai.llm.base import BaseLLM
from engram_ai.storage import BaseStorage

class MyLLM(BaseLLM):
    def generate(self, prompt: str) -> str:
        return my_model.complete(prompt)

forge = Forge(llm=MyLLM())
```

---

**Tech:** Python 3.10+, ChromaDB, Pydantic v2, Click, pytest, ruff
**License:** Apache 2.0

Would love feedback on the API design — especially the `crystallize()` / `evolve()` split and whether the valence model makes sense for different use cases.
```

## Flair
```
Intermediate Showcase
```
