# ProductHunt Launch

## Product Name
```
Engram-AI
```

## Tagline (60 chars max)
```
Experience-driven memory that makes AI agents learn from scars
```

## Description
```
Most AI memory systems work like a diary — they store facts. Engram-AI works like a scar — it stores *what the agent did*, *what happened*, and *whether it was good or bad*.

**How it works:**
1. **Record** — capture experiences with action, context, outcome, and valence (−1.0 to +1.0)
2. **Query** — retrieve past experiences partitioned into "best actions" and "things to avoid"
3. **Crystallize** — cluster similar experiences and extract reusable skill patterns via LLM
4. **Evolve** — write learned skills into the agent's config file (CLAUDE.md, AGENTS.md, etc.)

**For Claude Code users:** One command sets up automatic recording via hooks. Claude Code starts learning from every interaction immediately — no manual work needed.

**For developers:** A clean Python API (`pip install engram-forge`) with ChromaDB storage, optional Anthropic/OpenAI LLM integration, 10-tool MCP server, web dashboard, and multi-project support.

**No API key required for core features.** Keyword-based valence detection and clustering work completely offline.

Apache 2.0 | Python 3.10+ | v0.4.0
```

## First Comment (Maker's comment — most important)
```
Hey Product Hunt! 👋

I'm the creator of Engram-AI. I built this after getting frustrated watching AI agents make the same mistakes over and over, session after session.

The core insight: **memory and learning are different things**. Storing facts ("the user prefers Python") is memory. Recognizing "every time I used Optional types in API responses, the user rejected it" is learning. Engram-AI is built for the second one.

**The technical bits I'm most proud of:**

1. **Two-phase recording** — a PostToolUse hook records what the agent did, a UserPromptSubmit hook detects your reaction (positive/negative) from natural language. The agent learns from your responses without you having to explicitly rate anything.

2. **Tiered valence detection** — keyword matching (free, offline, EN+JP) → LLM fallback → default. Most reactions get classified without an API call.

3. **Crystallization** — ChromaDB clusters similar experiences, then an LLM extracts the generalizable rule. Falls back to keyword-frequency clustering if no API key. The result is a `Skill` object with a confidence score and evidence count.

4. **Evolution** — skills get written back to CLAUDE.md (or any config) with idempotent delimiter blocks. The agent gets permanently better.

**For Claude Code users** — setup is literally:
```
pip install "engram-forge[full]"
engram-forge setup
```
Restart Claude Code, and it starts learning from every session.

**For developers** — the `Forge` facade is the main API. Swap in any LLM via `BaseLLM`, any storage via `BaseStorage`. OpenAI example in the repo.

I'd love feedback on the crystallization UX — specifically whether the explicit `crystallize()` → `evolve()` two-step makes sense, or if it should be more automatic.

GitHub: https://github.com/kajaha06251020/Engram-AI
Discord: https://discord.gg/hGAcEfKqgq
```

## Topics / Tags
```
Artificial Intelligence
Developer Tools
Open Source
Python
Productivity
```

## Gallery images to prepare
```
1. Hero: "Today's AI memory is a diary. Engram-AI is a scar." with architecture diagram
2. Screenshot: record → query → crystallize → evolve flow
3. Screenshot: web dashboard (experience graph visualization)
4. Code snippet: 10-line quick start example
5. Screenshot: CLAUDE.md evolution before/after
```
