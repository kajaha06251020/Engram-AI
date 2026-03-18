# Reddit — r/ClaudeAI

## Title
```
I made Claude Code remember and learn from its own mistakes — one command setup, no API key required for core features
```

## Body
```
After getting frustrated with Claude Code repeating the same mistakes session after session, I built a memory layer that teaches it from experience — not just stored text.

**Setup is one command:**

```bash
pip install "engram-forge[full]"
engram-forge setup
# Restart Claude Code
```

That's it. Here's what happens automatically after that:

---

### How it works

**1. PostToolUse hook** fires after every tool use, recording what Claude did as a "pending experience":
- Tool name + file path → `action`
- Context inferred from the operation → `context`

**2. UserPromptSubmit hook** fires when you respond, detecting whether you were happy or not:
- "Perfect!" / "Great" → valence ~0.8 (positive)
- "That's wrong" / "No, don't" → valence ~-0.7 (negative)
- Falls back to Claude API for ambiguous reactions
- Completes the pending experience in ChromaDB

**3. Active recall** injects relevant past skills and warnings into Claude's context before it acts:

```
Relevant knowledge:
- Avoid Optional types in API response models (confidence: 0.85)
Past issues in similar context:
- Ran DELETE without WHERE clause (valence: -1.0)
```

**4. Automatic crystallization** — after enough experiences accumulate, patterns get extracted:

```
"Avoid Optional types in API response models"  confidence=0.85
"Use descriptive variable names in tests"       confidence=0.92
```

**5. Evolution** — skills get written back to CLAUDE.md automatically:

```markdown
<!-- engram-forge:start -->
## Learned Skills
- Avoid Optional types in API response models (confidence: 0.85)
- Use descriptive variable names in tests (confidence: 0.92)
<!-- engram-forge:end -->
```

---

### MCP tools available in Claude Code

Once the MCP server is running, Claude can also use these tools directly:

- `engram_query` — "What do I know about REST API design?"
- `engram_record` — manually record an important experience
- `engram_teach` — inject a rule directly
- `engram_status` — see how much it has learned
- ... and 6 more

---

### Works without API key

Core features use keyword-based valence detection (no API call). Crystallization falls back to keyword clustering. You only need `ANTHROPIC_API_KEY` for LLM-powered pattern extraction — and even then, it's optional.

---

**GitHub:** https://github.com/kajaha06251020/Engram-AI
**PyPI:** https://pypi.org/project/engram-forge/

Happy to answer questions about the hook integration or MCP setup.
```

## Flair
```
Tools & Extensions
```
