# Hacker News — Show HN

## Title
```
Show HN: Engram-AI – Experience-driven memory for AI agents (pip install engram-forge)
```

## Body (comment in the thread)
```
Hi HN,

I built Engram-AI because I kept running into the same problem: AI agents that forget everything between sessions and repeat the same mistakes.

Most memory solutions store text facts ("the user likes Python"). That's a diary. Engram-AI stores *experiences* — causal structures of what the agent did, what happened, and whether it was good or bad:

    Action:  Used Optional[str] in API response model
    Context: Designing REST endpoint
    Outcome: User rejected it — "no nulls in responses"
    Valence: -0.8

Over time, experiences crystallize into skills:

    "Avoid Optional types in API response models"  confidence=0.85

And skills evolve into the agent's config (CLAUDE.md), making it permanently better.

**Technical bits:**
- Storage: ChromaDB (cosine similarity for experience retrieval)
- Valence detection: tiered — keyword matching → LLM → default 0.3
- Crystallization: cluster similar experiences → LLM extracts the pattern (falls back to keyword-frequency clustering if no API key)
- Works as a Python library, CLI, or MCP server (10 tools)
- No Anthropic API key required for core features

**For Claude Code users:**
    pip install "engram-forge[full]"
    engram-forge setup
That's it — hooks record every tool use, detect valence from your reactions, and evolve CLAUDE.md automatically.

**For developers:**
    from engram_ai import Forge
    forge = Forge()
    forge.record(action=..., context=..., outcome=..., valence=0.9)
    forge.query("REST API design")     # → {best: [...], avoid: [...]}
    forge.crystallize()                # → [Skill(...)]
    forge.evolve("./CLAUDE.md")

The "diary vs. scar" framing came from thinking about how humans actually learn — we don't remember facts as well as we remember failures and wins. A neural engram is a physical trace of memory in the brain. That's the metaphor.

v0.4.0, Apache 2.0, Python 3.10+.

GitHub: https://github.com/kajaha06251020/Engram-AI
PyPI: https://pypi.org/project/engram-forge/

Happy to answer questions about the architecture or design decisions.
```

## Tags / Category
- Ask HN or Show HN
- Category: Ask (Show HN prefix handles it)

## Best time to post
- Tuesday–Thursday, 9–11am US Eastern time
```
