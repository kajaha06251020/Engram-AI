# Engram-AI pip + MCP Distribution Design

**Date:** 2026-03-18
**Status:** Draft
**Target Version:** v0.4.0

---

## Overview

Distribute Engram-AI as both a Python pip package and an MCP server, targeting two user types:

1. **Developers** — embed Engram-AI in their own apps via `from engram_ai import Forge`
2. **Claude Code users** — integrate persistent memory into Claude Code sessions via MCP

No Anthropic API key required for core functionality. Claude Code provides AI capabilities via MCP.

---

## Package Extras Structure

### Core (`pip install engram-ai`)

Required dependencies only:

| Package | Purpose |
|---------|---------|
| `chromadb>=0.5.0` | Vector storage for experiences and skills |
| `click>=8.0.0` | CLI framework |
| `pydantic>=2.0.0` | Data model validation |

**Excluded from core:** `anthropic`, `mcp`, `fastapi`, `uvicorn`

### Optional Extras

| Extra | Command | Adds | Use Case |
|-------|---------|------|---------|
| `mcp` | `pip install engram-ai[mcp]` | `mcp>=1.0.0` | Claude Code integration |
| `claude` | `pip install engram-ai[claude]` | `anthropic>=0.40.0` | External app AI processing |
| `dashboard` | `pip install engram-ai[dashboard]` | `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0` | Web UI |
| `dev` | `pip install engram-ai[dev]` | `pytest`, `pytest-asyncio`, `ruff`, `httpx` | Development tools |
| `full` | `pip install engram-ai[full]` | All of the above | Everything |

### Capabilities Without Extras

| Feature | Core only | + claude | + mcp |
|---------|-----------|----------|-------|
| `forge.record()` | ✅ keyword valence | ✅ LLM valence | ✅ |
| `forge.query()` | ✅ ChromaDB search | ✅ | ✅ |
| `forge.teach()` | ✅ | ✅ | ✅ |
| `forge.crystallize()` | ⚠️ keyword clusters only | ✅ LLM patterns | ✅ |
| `forge.evolve()` | ✅ writes CLAUDE.md | ✅ | ✅ |
| `forge.observe()` | ❌ requires LLM | ✅ | ✅ (via Claude Code) |
| MCP server | ❌ | ❌ | ✅ |

---

## Public API Surface

### Stable Public API (`from engram_ai import ...`)

```python
# Main entry points
from engram_ai import Forge           # Primary operations class
from engram_ai import ProjectManager  # Multi-project management

# Data models (returned by Forge methods)
from engram_ai import Experience
from engram_ai import Skill

# Extension points (for custom storage/LLM implementations)
from engram_ai.storage import BaseStorage
from engram_ai.llm import BaseLLM
```

### Forge Public Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `record` | `(action, context, outcome, valence?, project?) -> Experience` | Record an experience |
| `query` | `(context, k=5, project?) -> QueryResult` | Search past experiences |
| `crystallize` | `(min_experiences=3, min_confidence=0.7, project?) -> list[Skill]` | Extract skill patterns |
| `evolve` | `(config_path, project?) -> str` | Write skills to agent config |
| `teach` | `(rule, context_pattern, skill_type, confidence, project?) -> Skill` | Directly register a skill |
| `warn` | `(context, project?) -> list[Skill]` | Find similar skills as warnings |
| `observe` | `(messages, max_turns=3, project?) -> dict` | Auto-record from conversation |
| `status` | `(project?) -> dict` | Statistics summary |
| `detect_conflicts` | `(project?) -> list` | Find conflicting skills |
| `merge_skills` | `(skill_a_id, skill_b_id, project?) -> Skill` | Merge two skills |
| `apply_decay` | `(project?) -> list[Skill]` | Apply time-based confidence decay |

### Internal (Subject to Change Without Notice)

```
engram_ai.core.*       # Recorder, Querier, Crystallizer, Evolver
engram_ai.adapters.*   # Framework adapters (use via Forge.evolve())
engram_ai.policies.*   # DecayPolicy, ConflictPolicy
engram_ai.events.*     # EventBus, event constants
```

---

## MCP Server Distribution

### Installation Methods (Both Supported)

**Method A: uvx (no install required)**
```bash
uvx engram-ai[mcp]
```

**Method B: pip install + CLI**
```bash
pip install engram-ai[mcp]
engram-ai serve
```

### Claude Code Registration (`engram-ai setup` auto-configures)

The `engram-ai setup` command automatically adds to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "engram-ai": {
      "command": "uvx",
      "args": ["engram-ai[mcp]"],
      "env": {}
    }
  }
}
```

### MCP Tools (10 tools, current surface maintained)

| Tool | Input | Output |
|------|-------|--------|
| `engram_record` | action, context, outcome, valence?, project? | Experience ID |
| `engram_query` | context, k=5, project? | `{best: [...], avoid: [...]}` |
| `engram_crystallize` | min_experiences=3, min_confidence=0.7, project? | Skill list |
| `engram_evolve` | config_path, project? | Evolution diff string |
| `engram_observe` | messages, max_turns=3, project? | `{recorded, crystallized}` |
| `engram_teach` | rule, context_pattern, skill_type, confidence, project? | Skill object |
| `engram_status` | project? | Stats dict |
| `engram_conflicts` | project? | Skill pair list |
| `engram_merge` | skill_a_id, skill_b_id, project? | Merged Skill |
| `engram_decay` | project? | Updated skills list |

### MCP Behavior Without Anthropic API Key

When `ANTHROPIC_API_KEY` is not set:
- `engram_record`: uses keyword-based valence detection
- `engram_query`: returns ChromaDB vector search results
- `engram_crystallize`: returns keyword-clustered patterns only (degraded quality)
- `engram_observe`: **disabled** (requires LLM), returns error with clear message
- All other tools: fully functional

---

## Storage and Configuration

### Default Storage Path

```
~/.engram-ai/data/           # default
~/.engram-ai/data/{project}/ # per-project
```

Override via environment variable:
```bash
ENGRAM_AI_STORAGE=/custom/path engram-ai serve
```

### Configuration File

```json
// ~/.engram-ai/config.json
{
  "storage_path": "~/.engram-ai/data",
  "llm": {
    "provider": "claude",
    "model": "claude-opus-4-6"
  },
  "crystallize": {
    "min_experiences": 3,
    "min_confidence": 0.7
  }
}
```

---

## pyproject.toml Changes Required

```toml
[project]
name = "engram-ai"
version = "0.4.0"

dependencies = [
    "chromadb>=0.5.0",
    "click>=8.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
mcp = ["mcp>=1.0.0"]
claude = ["anthropic>=0.40.0"]
dashboard = ["fastapi>=0.115.0", "uvicorn[standard]>=0.30.0"]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.24.0", "ruff>=0.8.0", "httpx>=0.27.0"]
full = ["engram-ai[mcp,claude,dashboard]"]
```

---

## Files to Change

| File | Change |
|------|--------|
| `pyproject.toml` | Move `anthropic`, `mcp`, `fastapi`, `uvicorn` to optional extras |
| `src/engram_ai/__init__.py` | Add `BaseStorage`, `BaseLLM` to public exports |
| `src/engram_ai/llm/claude.py` | Guard import: `anthropic` only imported if installed |
| `src/engram_ai/mcp.py` | Guard import: `mcp` only imported if installed |
| `src/engram_ai/dashboard/server.py` | Guard import: `fastapi` only imported if installed |
| `src/engram_ai/cli.py` | `setup` command writes MCP config with `uvx` args |
| `src/engram_ai/core/recorder.py` | Graceful fallback when LLM not available |
| `src/engram_ai/core/crystallizer.py` | Graceful fallback to keyword clustering |
