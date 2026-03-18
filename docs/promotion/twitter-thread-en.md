# X (Twitter) — English Thread

## Tweet 1 (Hook)
```
Today's AI memory is a diary.

Engram-AI makes scars.

A thread on why that matters 🧵
```

## Tweet 2
```
Most AI memory systems store facts:
"The user prefers Python"
"This project uses REST"

That's fine for preferences.

But it doesn't help an agent learn from what it *did*.
```

## Tweet 3
```
Engram-AI stores experiences:

Action:  Used Optional[str] in API response model
Context: Designing REST endpoint
Outcome: User rejected — "no nulls please"
Valence: -0.8 ← the learning signal

Not what the agent knows. What it did. What happened. Whether it worked.
```

## Tweet 4
```
Over time, experiences crystallize into skills:

"Avoid Optional types in API response models"
confidence: 0.85
evidence: 5 experiences

Then skills evolve into the agent's config — making it permanently better.

The loop: record → query → crystallize → evolve
```

## Tweet 5
```
For Claude Code users, setup is one command:

pip install "engram-forge[full]"
engram-forge setup

Two hooks handle everything automatically:
→ PostToolUse: records what Claude did
→ UserPromptSubmit: detects whether you approved

No babysitting required.
```

## Tweet 6
```
For developers embedding it in apps:

from engram_ai import Forge

forge = Forge()
forge.record(action=..., context=..., outcome=..., valence=0.9)

result = forge.query("REST API design")
# → {"best": [...], "avoid": [...]}

skills = forge.crystallize()
forge.evolve("./CLAUDE.md")
```

## Tweet 7
```
No Anthropic API key required for core features.

Valence detection falls back to keyword matching (EN + JP).
Crystallization falls back to keyword clustering.

Works completely offline.

Add [claude] extra for LLM-powered pattern extraction.
```

## Tweet 8
```
10 MCP tools when running as a server:

engram_record / engram_query / engram_crystallize
engram_evolve / engram_teach / engram_observe
engram_status / engram_conflicts / engram_merge / engram_decay

Claude can query its own memory mid-conversation.
```

## Tweet 9
```
Plug in any LLM:

class MyLLM(BaseLLM):
    def generate(self, prompt: str) -> str:
        return my_model.complete(prompt)

forge = Forge(llm=MyLLM())

OpenAI example in the repo.
Multi-LLM support (Ollama etc.) coming soon.
```

## Tweet 10 (CTA)
```
pip install engram-forge

Apache 2.0. Python 3.10+. ChromaDB + Pydantic v2.

GitHub: https://github.com/kajaha06251020/Engram-AI
PyPI:   https://pypi.org/project/engram-forge/
Docs:   discord.gg/hGAcEfKqgq

If this is useful, a ⭐ goes a long way 🙏

#Python #AI #LLM #MachineLearning #OpenSource #ClaudeAI #MCP
```

## Hashtags (standalone post tags)
```
#Python #AI #LLM #AgentMemory #OpenSource #ClaudeAI #MCP #MachineLearning #BuildInPublic
```
