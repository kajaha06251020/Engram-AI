# Reddit — r/LocalLLaMA

## Title
```
I built an experience-driven memory layer for AI agents — stores what agents DID and whether it worked, not just facts (pip install engram-forge)
```

## Body
```
Most AI memory systems are glorified text search. They store facts: "the user prefers Python", "this project uses REST". That's fine for preferences, but it doesn't help an agent learn from its own behavior.

I wanted something different: memory that captures **causality**. What did the agent do? What was the context? What happened? Was it good or bad?

---

### The core model

```python
Experience(
    action  = "Used Optional[str] in API response model",
    context = "Designing REST endpoint for mobile client",
    outcome = "User rejected it — 'no null values in responses please'",
    valence = -0.8,   # ← the learning signal
)
```

Over time, similar experiences **crystallize** into skills:

```
Skill: "Avoid Optional types in API response models"
Confidence: 0.85
Evidence: 5 experiences (4 negative, 1 positive)
```

Skills then **evolve** into the agent's config file, making it permanently better at that pattern.

---

### How crystallization works

1. Query ChromaDB for all experiences
2. Cluster by cosine similarity
3. For each cluster with ≥3 experiences: ask LLM "what rule do these experiences suggest?"
4. Store the resulting Skill with confidence = avg(|valence|) in that cluster

No API key? Falls back to keyword-frequency clustering. Works offline.

---

### The valence detection pipeline

When you record an experience, valence isn't always known upfront (e.g. during Claude Code hook usage):

1. **Keyword matching** (free, offline) — detects positive/negative signals in EN + JP
2. **LLM fallback** — when keywords are ambiguous, calls Claude API
3. **Default 0.3** — mild positive assumption when both fail

The two-phase recording (PostToolUse hook → UserPromptSubmit hook) lets the agent separate *what it did* from *how the human reacted*.

---

### For Claude Code users

```bash
pip install "engram-forge[full]"
engram-forge setup
```

That's it. Two hooks get registered:
- `PostToolUse` → records the tool use as a pending experience
- `UserPromptSubmit` → detects valence from your next message, completes the experience

The MCP server exposes 10 tools so Claude can query its own memory mid-conversation.

---

### For everyone else

```python
from engram_ai import Forge

forge = Forge(storage_path="./my-agent-memory")
forge.record(action=..., context=..., outcome=..., valence=0.9)

result = forge.query("database query patterns")
# → {"best": [(exp, score), ...], "avoid": [(exp, score), ...]}

skills = forge.crystallize()
forge.evolve("./AGENT_INSTRUCTIONS.md")
```

Swap in any LLM by implementing `BaseLLM.generate()` + `extract_experience()`. OpenAI example in the repo.

---

**Stack:** Python 3.10+, ChromaDB, Pydantic v2, Click, MCP SDK (optional), FastAPI (optional dashboard)

**Links:**
- GitHub: https://github.com/kajaha06251020/Engram-AI
- PyPI: https://pypi.org/project/engram-forge/
- `pip install engram-forge` (core, no API key needed)
- `pip install "engram-forge[full]"` (everything)

Honest limitations: crystallization quality is much better with an LLM. The keyword fallback works but produces generic rule names. Multi-LLM support (OpenAI, Ollama) is on the roadmap.

Happy to dig into any technical details.
```

## Flair
```
Project
```
