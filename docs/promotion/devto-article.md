# Dev.to Article

## Title
```
I built an experience-driven memory layer for AI agents — here's why "diary" memory isn't enough
```

## Tags
```
ai, python, opensource, llm
```

## Cover image alt text
```
Engram-AI: Experience-driven memory for AI agents
```

---

## Article Body

# I built an experience-driven memory layer for AI agents — here's why "diary" memory isn't enough

Picture this: you've been working with your AI coding assistant for months. You've corrected the same mistake dozens of times. Every new session, it makes the same error again.

The problem isn't intelligence — it's memory architecture.

## The diary problem

Most AI memory systems work like a diary. They store text facts:

- "The user prefers Python over JavaScript"
- "This project uses REST APIs"
- "The team follows conventional commits"

These systems are essentially semantic search over stored text. They're useful for preferences and context, but they have a fundamental limitation: **they don't capture causality**.

They don't know that every time the agent used `Optional[str]` in an API response model, the user rejected it. They don't know that the one time it used raw SQL without parameterization, it caused a security review. They store *what the agent knows*, not *what the agent learned*.

## The scar model

Biological memory forms differently for experiences than for facts. A neural **engram** is a physical memory trace created by experience — especially by experiences with emotional valence (good or bad outcomes).

This is the model I built Engram-AI around. Instead of storing facts, it stores **experiences**:

```python
Experience(
    action  = "Used Optional[str] in API response model",
    context = "Designing REST endpoint for mobile client",
    outcome = "User rejected — 'no null values in responses please'",
    valence = -0.8,   # ← the learning signal
)
```

Four fields. But the key one is `valence` — a scalar from −1.0 (terrible outcome) to +1.0 (great outcome). This is the signal that makes learning possible.

## The four operations

Engram-AI is built around four operations:

### 1. Record

Store an experience with explicit valence:

```python
from engram_ai import Forge

forge = Forge()

forge.record(
    action="Used list comprehension for 10k-row CSV transform",
    context="Data processing pipeline with pandas",
    outcome="Fast and readable — user approved immediately",
    valence=0.9,
)
```

### 2. Query

Retrieve relevant past experiences, partitioned by outcome:

```python
result = forge.query("data transformation approach")

print("What worked:")
for exp, score in result["best"]:
    print(f"  [{score:.2f}] {exp.action}")

print("What to avoid:")
for exp, score in result["avoid"]:
    print(f"  [{score:.2f}] {exp.action}")
```

The query uses ChromaDB cosine similarity, then partitions results by valence. You get two lists: things that worked, and things that didn't.

### 3. Crystallize

Extract reusable skill patterns from accumulated experiences:

```python
skills = forge.crystallize(min_experiences=3, min_confidence=0.7)

for skill in skills:
    print(f"Learned: {skill.rule} (confidence={skill.confidence:.2f})")
# → Learned: "Prefer list comprehensions for data transforms" (confidence=0.87)
```

Under the hood: ChromaDB clusters similar experiences by cosine similarity. For each cluster with enough evidence and average |valence| above the confidence threshold, an LLM prompt asks "what rule do these experiences suggest?" The answer becomes a `Skill`.

No LLM? It falls back to keyword-frequency clustering. Works offline.

### 4. Evolve

Write learned skills into the agent's configuration file:

```python
record = forge.evolve(config_path="./CLAUDE.md")
```

This writes (or updates) a delimited block in CLAUDE.md:

```markdown
<!-- engram-forge:start -->
## Engram-AI: Learned Skills
- Prefer list comprehensions for data transforms (confidence: 0.87)
- Avoid Optional types in API response models (confidence: 0.85)
- Use descriptive variable names in test files (confidence: 0.92)
<!-- engram-forge:end -->
```

The next session, the agent reads these rules from its config and applies them from the start.

## For Claude Code users: zero-config setup

The most common use case is with Claude Code. Setup takes one command:

```bash
pip install "engram-forge[full]"
engram-forge setup
```

This registers two hooks in `~/.claude/settings.json`:

**PostToolUse hook** — fires after every tool use, recording what Claude did as a pending experience. No valence yet — we don't know if it worked.

**UserPromptSubmit hook** — fires when you send your next message. It detects your reaction (positive or negative) from natural language and completes the pending experience with the detected valence.

The valence detection is tiered:
1. Keyword matching (free, offline, EN + JP) — catches obvious signals like "perfect", "wrong", "approved", "no"
2. LLM fallback — for ambiguous reactions
3. Default 0.3 — mild positive assumption

The MCP server runs in parallel, exposing 10 tools that Claude can use mid-conversation:

```
engram_query       — "What do I know about REST API design?"
engram_record      — manually record an important experience
engram_teach       — inject a rule directly
engram_crystallize — trigger crystallization
engram_status      — see statistics
...and 5 more
```

## You don't need an API key

This was a deliberate design decision. Core features work without any LLM:

| Feature | With API key | Without |
|---------|-------------|---------|
| `record()` valence | LLM sentiment | Keyword matching |
| `query()` | ChromaDB search | Same |
| `crystallize()` | LLM pattern extraction | Keyword clustering |
| Everything else | Full | Full |

Install just the core:

```bash
pip install engram-forge
```

Add the Anthropic SDK when you're ready:

```bash
pip install "engram-forge[claude]"
export ANTHROPIC_API_KEY=sk-...
```

## Teaching rules directly

You don't have to wait for experiences to accumulate. You can teach rules directly:

```python
forge.teach(
    rule="Always validate user input at the API boundary",
    context_pattern="handling HTTP requests",
    skill_type="positive",
    confidence=0.95,
)

forge.teach(
    rule="Never run DELETE queries without a WHERE clause",
    context_pattern="database operations",
    skill_type="anti",
    confidence=1.0,
)
```

And check for past failures before acting:

```python
warnings = forge.warn(
    action="Run DELETE query on production database",
    context="Database maintenance",
    threshold=0.5,
)
if warnings:
    print("Past failures with similar actions:")
    for w in warnings:
        print(f"  [{w.valence:.1f}] {w.outcome}")
```

## Multi-project support

Each project gets isolated memory:

```python
from engram_ai import ProjectManager
from pathlib import Path

pm = ProjectManager(base_path=Path("~/.engram-ai/data"))

frontend = pm.get_forge("myapp/frontend")
backend  = pm.get_forge("myapp/backend")
```

Via CLI:
```bash
engram-forge -p myapp/frontend query "React component patterns"
engram-forge -p myapp/backend  crystallize
```

## Extending with your own LLM

The `BaseLLM` interface has two methods:

```python
from engram_ai.llm.base import BaseLLM

class OpenAILLM(BaseLLM):
    def generate(self, prompt: str) -> str:
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        ).choices[0].message.content

    def extract_experience(self, messages: list[dict]) -> dict | None:
        # Extract action/context/outcome/valence from conversation
        ...

forge = Forge(llm=OpenAILLM())
```

Full OpenAI example in the [examples directory](https://github.com/kajaha06251020/Engram-AI/blob/main/examples/06_custom_llm.py).

## The honest limitations

- **Crystallization quality** depends heavily on LLM quality. The keyword fallback works but produces generic rule names.
- **Valence is a scalar.** Richer affect models might capture more nuance. This is on the roadmap.
- **No formal benchmarks yet.** This is early-stage infrastructure. I'm working on evaluation.
- **The clustering approach is greedy.** Better algorithms would improve skill quality.

## Install and try it

```bash
# Core — no API key needed
pip install engram-forge

# For Claude Code integration
pip install "engram-forge[full]"
engram-forge setup

# For Python library use with Anthropic
pip install "engram-forge[claude]"
```

**GitHub:** https://github.com/kajaha06251020/Engram-AI
**PyPI:** https://pypi.org/project/engram-forge/
**Discord:** https://discord.gg/hGAcEfKqgq

Apache 2.0. Python 3.10+. v0.4.0.

I'd love feedback — especially on the `crystallize()` → `evolve()` split, the valence model, and whether the two-phase hook recording makes sense for other use cases. Drop a comment or open an issue!
