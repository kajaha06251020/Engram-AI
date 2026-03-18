# Discord 投稿メッセージ

---

## Anthropic Discord — #showcase または #tools チャンネル

```
Hey everyone! 👋

I built **Engram-AI** — an experience-driven memory layer that lets AI agents learn from their own mistakes, not just store text facts.

**The core idea:** Instead of storing "user prefers X", it stores *what the agent did*, *what happened*, and *whether it worked* (valence −1.0 to +1.0). Over time, experiences crystallize into skills, which evolve into the agent's config.

**For Claude Code users, setup is one command:**
```
pip install "engram-forge[full]"
engram-forge setup
```
Two hooks record every tool use and detect your reactions automatically. The MCP server exposes 10 tools for Claude to query its own memory.

**No API key needed for core features** — keyword-based valence detection and clustering work offline.

- GitHub: https://github.com/kajaha06251020/Engram-AI
- PyPI: https://pypi.org/project/engram-forge/ (`pip install engram-forge`)
- Discord: https://discord.gg/hGAcEfKqgq

Would love feedback from the Claude ecosystem — especially on the MCP tool design and the hook integration. Happy to answer questions!
```

---

## AI/LLM系 Discord コミュニティ（汎用）

```
🧠 **Engram-AI** — Experience-driven memory for AI agents

Most memory systems store facts. Engram-AI stores *causality*:

```python
forge.record(
    action="Used Optional[str] in API response",
    context="REST endpoint design",
    outcome="User rejected — 'no nulls please'",
    valence=-0.8,
)
```

Experiences → crystallize into skills → evolve into agent config.

✅ Works with Claude Code (MCP + hooks)
✅ No API key required for core features
✅ Custom LLM support (OpenAI, Ollama, etc.)
✅ Multi-project isolation
✅ Web dashboard with neural graph

`pip install engram-forge`
https://github.com/kajaha06251020/Engram-AI
```
