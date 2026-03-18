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
| `full` | `pip install engram-ai[full]` | mcp + claude + dashboard (not dev) | Everything except dev tools |

Note: `dev` is intentionally excluded from `full`. Use `pip install engram-ai[full,dev]` for development.

### Capabilities Without Extras

| Feature | Core only | + claude | + mcp |
|---------|-----------|----------|-------|
| `forge.record()` | ✅ keyword valence | ✅ LLM valence | ✅ |
| `forge.query()` | ✅ ChromaDB search | ✅ | ✅ |
| `forge.teach()` | ✅ | ✅ | ✅ |
| `forge.crystallize()` | ⚠️ keyword clusters only (requires implementation) | ✅ LLM patterns | ✅ |
| `forge.evolve()` | ✅ writes CLAUDE.md | ✅ | ✅ |
| `forge.observe()` | ❌ requires LLM | ✅ | ✅ (via Claude Code) |
| MCP server | ❌ | ❌ | ✅ |

Note: Core-only keyword clustering for `crystallize()` requires a new `KeywordCrystallizer` fallback implementation.

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
from engram_ai import QueryResult     # Return type of forge.query() / forge.recall()

# Extension points (for custom storage/LLM implementations)
from engram_ai.storage import BaseStorage
from engram_ai.llm import BaseLLM
```

### Forge Public Methods

Note: `project?` parameter shown in the MCP tools table is a routing parameter handled by `ProjectManager`, not a native `Forge` method parameter. Individual `Forge` instances are project-scoped.

| Method | Signature | Description |
|--------|-----------|-------------|
| `record` | `(action, context, outcome, valence: float) -> Experience` | Record an experience (valence required) |
| `query` | `(context, k=5) -> QueryResult` | Search past experiences |
| `crystallize` | `(min_experiences=3, min_confidence=0.7) -> list[Skill]` | Extract skill patterns |
| `evolve` | `(config_path) -> EvolutionRecord \| None` | Write skills to agent config |
| `teach` | `(rule, context_pattern, skill_type, confidence) -> Skill` | Directly register a skill |
| `warn` | `(action, context, threshold=0.6) -> list[Experience]` | Find negative past experiences as warnings |
| `observe` | `(messages, max_turns=3, crystallize_threshold=5) -> dict` | Auto-record from conversation |
| `status` | `() -> dict` | Statistics summary |
| `detect_conflicts` | `() -> list` | Find conflicting skills |
| `merge_skills` | `(skill_a_id, skill_b_id) -> Skill` | Merge two skills |
| `apply_decay` | `() -> list[Skill]` | Apply time-based confidence decay |

Methods `recall()` and `check_skill_effectiveness()` exist in the current implementation but are used internally by hooks. These will be prefixed `_` to signal internal use.

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

**Method A: uvx (no install required, ephemeral)**
```bash
# Note: quote the extras argument if your shell requires it
uvx "engram-ai[mcp]"
```

**Method B: pip install + CLI (recommended for regular use)**
```bash
pip install engram-ai[mcp]
engram-ai serve
```

### Claude Code Registration (`engram-ai setup` auto-configures)

The `engram-ai setup` command automatically adds to `~/.claude/settings.json`.
Default uses `engram-ai serve` (pip-installed path):

```json
{
  "mcpServers": {
    "engram-ai": {
      "command": "engram-ai",
      "args": ["serve"]
    }
  }
}
```

A `--uvx` boolean flag (`is_flag=True`) enables the uvx path for users who prefer not to pip install:

```json
{
  "mcpServers": {
    "engram-ai": {
      "command": "uvx",
      "args": ["engram-ai[mcp]"]
    }
  }
}
```

### MCP Tools (10 tools, current surface maintained)

| Tool | Input | Output |
|------|-------|--------|
| `engram_record` | action, context, outcome, valence, project? | Experience ID |
| `engram_query` | context, k=5, project? | `{best: [...], avoid: [...]}` |
| `engram_crystallize` | min_experiences=3, min_confidence=0.7, project? | Skill list |
| `engram_evolve` | config_path, project? | Evolution diff string |
| `engram_observe` | messages, max_turns=3, crystallize_threshold=5, project? | `{recorded, crystallized}` |
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
- `engram_observe`: **partially disabled** — the record sub-step runs in keyword-valence mode, but the LLM extraction step fails; the whole tool returns an error with a clear message (`pip install engram-ai[claude]`) rather than partially recording
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
    "model": "claude-sonnet-4-6"
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
| `src/engram_ai/__init__.py` | Add `BaseStorage`, `BaseLLM` to public exports; add `QueryResult` (currently in `engram_ai.core.querier`) to public exports |
| `src/engram_ai/forge.py` | Lazy import `ClaudeLLM` (only when `anthropic` installed); `Forge.__init__` defaults `llm` to `None` when `anthropic` not installed — raises `ImportError` with install hint (`pip install engram-ai[claude]`) at construction time if `anthropic` is absent and no `llm` is passed; rename `recall` → `_recall`, `check_skill_effectiveness` → `_check_skill_effectiveness` |
| `src/engram_ai/project.py` | Change `llm: BaseLLM` to `llm: BaseLLM \| None = None` in `__init__` signature |
| `src/engram_ai/llm/claude.py` | Guard: raise `ImportError` with install hint if `anthropic` not installed |
| `src/engram_ai/mcp.py` | Guard: raise `ImportError` with install hint if `mcp` not installed |
| `src/engram_ai/dashboard/server.py` | Guard: raise `ImportError` with install hint if `fastapi` not installed |
| `src/engram_ai/dashboard/api.py` | Guard: raise `ImportError` with install hint if `fastapi` not installed |
| `src/engram_ai/cli.py` | `setup` command writes `engram-ai serve` by default; add `--uvx` flag for uvx path |
| `src/engram_ai/core/recorder.py` | Graceful fallback when `llm` is `None` (keyword valence) |
| `src/engram_ai/core/crystallizer.py` | Add `KeywordCrystallizer` fallback; use when `llm` is `None` |
