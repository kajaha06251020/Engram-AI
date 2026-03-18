# pip + MCP Distribution Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure Engram-AI so `pip install engram-ai` works without Anthropic/MCP/FastAPI, with those as optional extras, and `engram-ai setup --uvx` configures Claude Code with one command.

**Architecture:** Move heavy dependencies (`anthropic`, `mcp`, `fastapi`, `uvicorn`) to optional extras. Guard each module with a try/except at import time. Add keyword-based crystallize fallback so core-only users get degraded-but-working behavior. Rename internal Forge methods with `_` prefix.

**Tech Stack:** Python 3.10+, hatchling, pytest, click, chromadb, pydantic

---

## File Map

| File | Action | Change |
|------|--------|--------|
| `pyproject.toml` | Modify | Move `anthropic`, `mcp`, `fastapi`, `uvicorn` to optional extras; bump version to 0.4.0 |
| `src/engram_ai/__init__.py` | Modify | Export `BaseStorage`, `BaseLLM`, `QueryResult` |
| `src/engram_ai/forge.py` | Modify | Lazy `ClaudeLLM` import; `ImportError` when no key and no llm; rename `recall`→`_recall`, `check_skill_effectiveness`→`_check_skill_effectiveness` |
| `src/engram_ai/project.py` | Modify | `llm: BaseLLM \| None = None` |
| `src/engram_ai/llm/claude.py` | Modify | Guard `import anthropic` with try/except → `ImportError` with install hint |
| `src/engram_ai/mcp.py` | Modify | Guard `from mcp.server import Server` with try/except → `ImportError` with install hint |
| `src/engram_ai/dashboard/server.py` | Modify | Guard `fastapi` import with try/except → `ImportError` with install hint |
| `src/engram_ai/dashboard/api.py` | Modify | Guard `fastapi` import with try/except → `ImportError` with install hint |
| `src/engram_ai/core/crystallizer.py` | Modify | Accept `llm: BaseLLM \| None`; keyword fallback when `llm` is None |
| `src/engram_ai/cli.py` | Modify | Add `--uvx` boolean flag to `setup` command |
| `tests/test_distribution.py` | Create | All new distribution-related tests |

---

### Task 1: Restructure pyproject.toml

**Files:**
- Modify: `pyproject.toml`

No tests needed — this is a pure metadata change. Run install after to confirm.

- [ ] **Step 1: Update pyproject.toml**

Replace the `[project]` dependencies block and add extras:

```toml
[project]
name = "engram-ai"
version = "0.4.0"
description = "Experience-driven memory infrastructure for AI agents"
license = "Apache-2.0"
requires-python = ">=3.10"
keywords = ["ai", "agent", "memory", "experience", "learning"]

dependencies = [
    "chromadb>=0.5.0",
    "click>=8.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
mcp = ["mcp>=1.0.0"]
claude = ["anthropic>=0.40.0"]
dashboard = ["fastapi>=0.115.0", "uvicorn[standard]>=0.30.0"]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
    "httpx>=0.27.0",
]
full = ["engram-ai[mcp,claude,dashboard]"]
```

- [ ] **Step 2: Verify package still installs**

```bash
cd /f/playground/Engram-AI
pip install -e ".[dev]" --quiet
python -c "import engram_ai; print('ok')"
```

Expected: `ok` (chromadb, click, pydantic available)

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat: restructure dependencies as optional extras (v0.4.0)"
```

---

### Task 2: Guard `llm/claude.py` against missing `anthropic`

**Files:**
- Modify: `src/engram_ai/llm/claude.py`
- Test: `tests/test_distribution.py` (create)

- [ ] **Step 1: Write failing test**

Create `tests/test_distribution.py`:

```python
"""Tests for optional extras distribution behavior."""
import sys
import pytest


class TestClaudeLLMImportGuard:
    def test_raises_import_error_when_anthropic_missing(self, monkeypatch):
        """ClaudeLLM raises ImportError with install hint when anthropic not installed."""
        monkeypatch.setitem(sys.modules, "anthropic", None)
        # Need to reload the module with anthropic blocked
        import importlib
        import engram_ai.llm.claude as claude_mod
        importlib.reload(claude_mod)
        with pytest.raises(ImportError, match="pip install engram-ai\\[claude\\]"):
            claude_mod.ClaudeLLM()

    def test_works_when_anthropic_available(self):
        """ClaudeLLM instantiates normally when anthropic is installed."""
        try:
            from engram_ai.llm.claude import ClaudeLLM
            llm = ClaudeLLM(api_key="sk-test")
            assert llm is not None
        except ImportError:
            pytest.skip("anthropic not installed")
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /f/playground/Engram-AI
pytest tests/test_distribution.py::TestClaudeLLMImportGuard -v
```

Expected: FAIL — `ClaudeLLM()` does not currently raise `ImportError` with that message

- [ ] **Step 3: Add guard to `llm/claude.py`**

Replace the top of `src/engram_ai/llm/claude.py`.
Note: This also updates the default model string from `claude-sonnet-4-20250514` to `claude-sonnet-4-6` per the v0.4.0 spec.

```python
import json
import logging
try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

from engram_ai.exceptions import LLMError
from engram_ai.llm.base import BaseLLM
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill

logger = logging.getLogger(__name__)

class ClaudeLLM(BaseLLM):
    """Claude API implementation for Engram-AI LLM operations."""
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        if anthropic is None:
            raise ImportError(
                "anthropic package is required for ClaudeLLM. "
                "Install it with: pip install engram-ai[claude]"
            )
        try:
            self._client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            raise LLMError(f"Failed to initialize Anthropic client: {e}") from e
        self._model = model
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_distribution.py::TestClaudeLLMImportGuard::test_raises_import_error_when_anthropic_missing -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/engram_ai/llm/claude.py tests/test_distribution.py
git commit -m "feat: guard ClaudeLLM import when anthropic not installed"
```

---

### Task 3: Guard `mcp.py` against missing `mcp`

**Files:**
- Modify: `src/engram_ai/mcp.py`
- Test: `tests/test_distribution.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_distribution.py`:

```python
class TestMCPImportGuard:
    def test_raises_import_error_when_mcp_missing(self, monkeypatch):
        """create_mcp_server raises ImportError with install hint when mcp not installed."""
        monkeypatch.setitem(sys.modules, "mcp", None)
        monkeypatch.setitem(sys.modules, "mcp.server", None)
        monkeypatch.setitem(sys.modules, "mcp.server.stdio", None)
        monkeypatch.setitem(sys.modules, "mcp.types", None)
        import importlib
        import engram_ai.mcp as mcp_mod
        importlib.reload(mcp_mod)
        with pytest.raises(ImportError, match="pip install engram-ai\\[mcp\\]"):
            mcp_mod.create_mcp_server(None)
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_distribution.py::TestMCPImportGuard -v
```

Expected: FAIL

- [ ] **Step 3: Add guard to `mcp.py`**

Replace the top of `src/engram_ai/mcp.py`:

```python
import logging

logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


def create_mcp_server(project_manager):
    """Create an MCP server exposing Engram-AI tools."""
    if not _MCP_AVAILABLE:
        raise ImportError(
            "mcp package is required for MCP server. "
            "Install it with: pip install engram-ai[mcp]"
        )
    server = Server("engram-ai")
    # ... rest of function unchanged


async def run_mcp_server():
    """Entry point for MCP server. Guard at top of function body."""
    if not _MCP_AVAILABLE:
        raise ImportError(
            "mcp package is required for MCP server. "
            "Install it with: pip install engram-ai[mcp]"
        )
    # ... rest of function unchanged
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_distribution.py::TestMCPImportGuard -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/engram_ai/mcp.py tests/test_distribution.py
git commit -m "feat: guard MCP server import when mcp not installed"
```

---

### Task 4: Guard dashboard against missing `fastapi`

**Files:**
- Modify: `src/engram_ai/dashboard/server.py`
- Modify: `src/engram_ai/dashboard/api.py`
- Test: `tests/test_distribution.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_distribution.py`:

```python
class TestDashboardImportGuard:
    def test_server_raises_import_error_when_fastapi_missing(self, monkeypatch):
        """Dashboard server raises ImportError with install hint when fastapi missing."""
        monkeypatch.setitem(sys.modules, "fastapi", None)
        import importlib
        import engram_ai.dashboard.server as server_mod
        importlib.reload(server_mod)
        with pytest.raises(ImportError, match="pip install engram-ai\\[dashboard\\]"):
            server_mod.create_app(None)

    def test_api_raises_import_error_when_fastapi_missing(self, monkeypatch):
        """Dashboard API raises ImportError with install hint when fastapi missing."""
        monkeypatch.setitem(sys.modules, "fastapi", None)
        import importlib
        import engram_ai.dashboard.api as api_mod
        importlib.reload(api_mod)
        with pytest.raises(ImportError, match="pip install engram-ai\\[dashboard\\]"):
            api_mod.create_router(None)
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_distribution.py::TestDashboardImportGuard -v
```

Expected: FAIL

- [ ] **Step 3: Add guard to `dashboard/server.py`**

Wrap the fastapi imports at the top of `src/engram_ai/dashboard/server.py`:

```python
try:
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
```

At the start of `create_app()`:

```python
def create_app(project_manager):
    if not _FASTAPI_AVAILABLE:
        raise ImportError(
            "fastapi package is required for the dashboard. "
            "Install it with: pip install engram-ai[dashboard]"
        )
    # ... rest unchanged
```

- [ ] **Step 4: Add guard to `dashboard/api.py`**

**Note:** `dashboard/api.py` uses a module-level `router = APIRouter(...)` pattern, not a `create_router()` function. The guard must wrap the fastapi imports AND the `APIRouter(...)` call must be deferred inside a factory function `create_router()` that you introduce. The test calls `api_mod.create_router(None)`.

Wrap the fastapi imports at the top of `src/engram_ai/dashboard/api.py`:

```python
try:
    from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
    from starlette.requests import Request
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
```

At the start of `create_router()`:

```python
def create_router(project_manager):
    if not _FASTAPI_AVAILABLE:
        raise ImportError(
            "fastapi package is required for the dashboard. "
            "Install it with: pip install engram-ai[dashboard]"
        )
    # ... rest unchanged
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_distribution.py::TestDashboardImportGuard -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/engram_ai/dashboard/server.py src/engram_ai/dashboard/api.py tests/test_distribution.py
git commit -m "feat: guard dashboard imports when fastapi not installed"
```

---

### Task 5: Keyword fallback in `crystallizer.py`

**Files:**
- Modify: `src/engram_ai/core/crystallizer.py`
- Test: `tests/core/test_crystallizer.py`

- [ ] **Step 1: Write failing test**

Append to `tests/core/test_crystallizer.py`:

```python
class TestKeywordFallback:
    def test_crystallize_without_llm_returns_keyword_skills(self, tmp_path):
        """Crystallizer with llm=None returns keyword-based skills."""
        from engram_ai.storage.chromadb import ChromaDBStorage
        from engram_ai.events.bus import EventBus
        from engram_ai.core.crystallizer import Crystallizer
        from engram_ai.models.experience import Experience

        storage = ChromaDBStorage(persist_path=str(tmp_path))
        event_bus = EventBus()
        crystallizer = Crystallizer(storage=storage, event_bus=event_bus, llm=None)

        # Add enough experiences to trigger crystallization
        for i in range(5):
            exp = Experience(
                action="use pytest for testing",
                context="writing unit tests for Python code",
                outcome="tests pass",
                valence=0.9,
            )
            storage.store_experience(exp)

        skills = crystallizer.crystallize(min_experiences=3, min_confidence=0.4)
        assert len(skills) >= 1
        assert skills[0].rule  # non-empty rule
        assert 0.0 <= skills[0].confidence <= 1.0

    def test_crystallize_without_llm_skips_below_threshold(self, tmp_path):
        """Keyword skills below min_confidence threshold are not returned."""
        from engram_ai.storage.chromadb import ChromaDBStorage
        from engram_ai.events.bus import EventBus
        from engram_ai.core.crystallizer import Crystallizer
        from engram_ai.models.experience import Experience

        storage = ChromaDBStorage(persist_path=str(tmp_path))
        event_bus = EventBus()
        crystallizer = Crystallizer(storage=storage, event_bus=event_bus, llm=None)

        for i in range(4):
            exp = Experience(
                action="deploy to production",
                context="CI pipeline finished",
                outcome="deployed",
                valence=0.8,
            )
            storage.store_experience(exp)

        # min_confidence=0.9 is above what keyword fallback produces (0.55)
        skills = crystallizer.crystallize(min_experiences=3, min_confidence=0.9)
        assert skills == []
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/core/test_crystallizer.py::TestKeywordFallback -v
```

Expected: FAIL — `Crystallizer` does not accept `llm=None`

- [ ] **Step 3: Add keyword fallback to `crystallizer.py`**

Change the `__init__` signature and add `_keyword_crystallize_pattern`:

```python
from collections import Counter
import re as _re

class Crystallizer:
    """Extracts skill patterns from accumulated experiences."""
    def __init__(
        self, storage: BaseStorage, event_bus: EventBus, llm: BaseLLM | None
    ) -> None:
        self._storage = storage
        self._event_bus = event_bus
        self._llm = llm

    def _keyword_crystallize_pattern(self, cluster: list[Experience]) -> Skill | None:
        """Fallback: extract a skill using keyword frequency when no LLM available."""
        stopwords = {
            "the", "a", "an", "to", "for", "of", "in", "on", "at", "is",
            "was", "are", "be", "it", "i", "you", "we", "this", "that",
        }
        words: list[str] = []
        for exp in cluster:
            words.extend(_re.findall(r"[a-zA-Z\u3040-\u9fff]+", exp.action.lower()))
            words.extend(_re.findall(r"[a-zA-Z\u3040-\u9fff]+", exp.context.lower()))
        top = [w for w, _ in Counter(words).most_common(10) if w not in stopwords][:5]
        if not top:
            return None
        avg_valence = sum(e.valence for e in cluster) / len(cluster)
        skill_type = "positive" if avg_valence >= 0 else "anti"
        rule = f"Pattern observed in similar experiences: {', '.join(top)}"
        context_pattern = " ".join(top)
        # valence_summary is a dict with "positive" and "negative" float keys
        pos = max(avg_valence, 0.0)
        neg = abs(min(avg_valence, 0.0))
        return Skill(
            rule=rule,
            context_pattern=context_pattern,
            confidence=0.55,
            source_experiences=[e.id for e in cluster],
            evidence_count=len(cluster),
            valence_summary={"positive": pos, "negative": neg},
            skill_type=skill_type,
        )
```

In `crystallize()`, replace `self._llm.crystallize_pattern(cluster)` with:

```python
if self._llm is not None:
    skill = self._llm.crystallize_pattern(cluster)
else:
    skill = self._keyword_crystallize_pattern(cluster)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/core/test_crystallizer.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/engram_ai/core/crystallizer.py tests/core/test_crystallizer.py
git commit -m "feat: keyword fallback in Crystallizer when llm=None"
```

---

### Task 6: Lazy `ClaudeLLM` import and method renames in `forge.py`

**Files:**
- Modify: `src/engram_ai/forge.py`
- Test: `tests/test_distribution.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_distribution.py`:

```python
class TestForgeWithoutAnthropic:
    def test_forge_raises_helpful_error_when_no_llm_and_no_anthropic(self, monkeypatch, tmp_path):
        """Forge() with no llm and no anthropic raises ImportError with install hint."""
        monkeypatch.setitem(sys.modules, "anthropic", None)
        import importlib
        import engram_ai.llm.claude as claude_mod
        import engram_ai.forge as forge_mod
        importlib.reload(claude_mod)
        importlib.reload(forge_mod)
        with pytest.raises(ImportError, match="pip install engram-ai\\[claude\\]"):
            forge_mod.Forge(storage_path=str(tmp_path))

    def test_forge_works_with_explicit_llm(self, tmp_path):
        """Forge(llm=mock) works without anthropic."""
        from tests.conftest import MockLLM
        from engram_ai.forge import Forge
        forge = Forge(llm=MockLLM(), storage_path=str(tmp_path))
        assert forge is not None

    def test_forge_succeeds_when_anthropic_installed_but_no_key(self, tmp_path):
        """Forge() with anthropic installed but no API key succeeds at construction.
        The client is created with api_key=None (uses env var if available).
        Fails only at API call time, not at construction time.
        """
        try:
            import anthropic  # noqa: F401
        except ImportError:
            pytest.skip("anthropic not installed")
        from engram_ai.forge import Forge
        # Should NOT raise — construction is lazy
        forge = Forge(storage_path=str(tmp_path))
        assert forge is not None

    def test_recall_is_private(self, tmp_path):
        """recall() is renamed to _recall() and not publicly accessible."""
        from tests.conftest import MockLLM
        from engram_ai.forge import Forge
        forge = Forge(llm=MockLLM(), storage_path=str(tmp_path))
        assert hasattr(forge, "_recall")
        assert not hasattr(forge, "recall")

    def test_check_skill_effectiveness_is_private(self, tmp_path):
        """check_skill_effectiveness() renamed to _check_skill_effectiveness()."""
        from tests.conftest import MockLLM
        from engram_ai.forge import Forge
        forge = Forge(llm=MockLLM(), storage_path=str(tmp_path))
        assert hasattr(forge, "_check_skill_effectiveness")
        assert not hasattr(forge, "check_skill_effectiveness")
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_distribution.py::TestForgeWithoutAnthropic -v
```

Expected: FAIL

- [ ] **Step 3: Update `forge.py`**

Remove the top-level `from engram_ai.llm.claude import ClaudeLLM` import (line 15).

In `Forge.__init__`, replace:

```python
self._llm = llm or ClaudeLLM(api_key=anthropic_api_key)
```

with:

```python
if llm is not None:
    self._llm = llm
elif anthropic_api_key is not None:
    from engram_ai.llm.claude import ClaudeLLM
    self._llm = ClaudeLLM(api_key=anthropic_api_key)
else:
    # Try to use ClaudeLLM with env key; raise helpful error if anthropic missing
    try:
        from engram_ai.llm.claude import ClaudeLLM
        self._llm = ClaudeLLM()
    except ImportError:
        raise ImportError(
            "No LLM provided and anthropic package is not installed. "
            "Either pass llm= explicitly, or install: pip install engram-ai[claude]"
        )
```

Rename methods by changing their `def` lines:
- `def recall(` → `def _recall(`
- `def check_skill_effectiveness(` → `def _check_skill_effectiveness(`

Update all callers of these methods:
- Within `forge.py`: search for `self.check_skill_effectiveness(` (line ~101) and change to `self._check_skill_effectiveness(`
- In `src/engram_ai/cli.py` line 364: change `forge.recall(user_message)` → `forge._recall(user_message)`

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_distribution.py::TestForgeWithoutAnthropic -v
pytest tests/test_forge.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/engram_ai/forge.py tests/test_distribution.py
git commit -m "feat: lazy ClaudeLLM import in Forge, rename internal methods to _private"
```

---

### Task 7: Update `project.py` signature

**Files:**
- Modify: `src/engram_ai/project.py`
- Test: `tests/test_project.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_project.py`:

```python
def test_project_manager_works_without_llm(tmp_path):
    """ProjectManager(base_path, config={}) works with llm defaulting to None."""
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, config={"default_project": "default"})
    assert pm is not None
    # get_forge should work (Forge will try lazy import but succeed or use None)
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_project.py::test_project_manager_works_without_llm -v
```

Expected: FAIL — `ProjectManager.__init__` requires `llm` positional arg

- [ ] **Step 3: Update `project.py`**

Replace the entire `__init__` method (lines 17-22):

```python
def __init__(self, base_path: Path, llm: BaseLLM | None = None, config: dict | None = None) -> None:
    self._base_path = Path(base_path)
    self._llm = llm
    self._config = config or {}
    self._default_project = self._config.get("default_project", "default")
    self._cache: dict[str, Forge] = {}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_project.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/engram_ai/project.py tests/test_project.py
git commit -m "feat: make llm optional in ProjectManager (default None)"
```

---

### Task 8: Expand `__init__.py` public exports

**Files:**
- Modify: `src/engram_ai/__init__.py`
- Test: `tests/test_distribution.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_distribution.py`:

```python
class TestPublicAPI:
    def test_base_storage_importable(self):
        from engram_ai.storage import BaseStorage
        assert BaseStorage is not None

    def test_base_llm_importable(self):
        from engram_ai.llm import BaseLLM
        assert BaseLLM is not None

    def test_query_result_importable(self):
        from engram_ai import QueryResult
        assert QueryResult is not None

    def test_all_exports_present(self):
        import engram_ai
        for name in ["Forge", "Experience", "Skill", "ProjectManager", "QueryResult"]:
            assert hasattr(engram_ai, name), f"Missing export: {name}"
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_distribution.py::TestPublicAPI -v
```

Expected: FAIL on `QueryResult` import from `engram_ai`

- [ ] **Step 3: Update `__init__.py`**

```python
"""Engram-AI: Experience-driven memory infrastructure for AI agents."""

__version__ = "0.4.0"

from engram_ai.forge import Forge
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill
from engram_ai.project import ProjectManager
from engram_ai.core.querier import QueryResult

__all__ = ["Forge", "Experience", "Skill", "ProjectManager", "QueryResult"]
```

Note: `BaseStorage` and `BaseLLM` are importable from `engram_ai.storage` and `engram_ai.llm` respectively — they don't need to be in the top-level namespace.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_distribution.py::TestPublicAPI -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/engram_ai/__init__.py tests/test_distribution.py
git commit -m "feat: add QueryResult to public API exports"
```

---

### Task 9: Add `--uvx` flag to `setup` command in `cli.py`

**Files:**
- Modify: `src/engram_ai/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_cli.py`:

```python
def test_setup_uvx_flag_writes_uvx_config(tmp_path, monkeypatch):
    """setup --uvx writes uvx-based MCP server config."""
    from click.testing import CliRunner
    from engram_ai.cli import main

    # Point settings to tmp dir
    fake_settings = tmp_path / ".claude" / "settings.json"
    fake_settings.parent.mkdir(parents=True)
    fake_config_dir = tmp_path / ".engram-ai"

    monkeypatch.setattr("engram_ai.cli.CONFIG_DIR", fake_config_dir)
    monkeypatch.setattr("engram_ai.cli.CONFIG_FILE", fake_config_dir / "config.json")

    import pathlib
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--uvx"])
    assert result.exit_code == 0

    import json
    settings = json.loads(fake_settings.read_text())
    mcp = settings["mcpServers"]["engram-ai"]
    assert mcp["command"] == "uvx"
    assert "engram-ai[mcp]" in mcp["args"]


def test_setup_default_writes_engram_serve_config(tmp_path, monkeypatch):
    """setup (no flags) writes engram-ai serve config."""
    from click.testing import CliRunner
    from engram_ai.cli import main

    fake_settings = tmp_path / ".claude" / "settings.json"
    fake_settings.parent.mkdir(parents=True)
    fake_config_dir = tmp_path / ".engram-ai"

    monkeypatch.setattr("engram_ai.cli.CONFIG_DIR", fake_config_dir)
    monkeypatch.setattr("engram_ai.cli.CONFIG_FILE", fake_config_dir / "config.json")

    import pathlib
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["setup"])
    assert result.exit_code == 0

    import json
    settings = json.loads(fake_settings.read_text())
    mcp = settings["mcpServers"]["engram-ai"]
    assert mcp["command"] == "engram-ai"
    assert mcp["args"] == ["serve"]
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_cli.py::test_setup_uvx_flag_writes_uvx_config tests/test_cli.py::test_setup_default_writes_engram_serve_config -v
```

Expected: FAIL — no `--uvx` flag exists

- [ ] **Step 3: Update `setup` command in `cli.py`**

```python
@main.command()
@click.option("--uvx", "use_uvx", is_flag=True, default=False,
              help="Configure MCP server to use uvx instead of pip-installed engram-ai.")
def setup(use_uvx: bool):
    """Auto-configure Engram-AI for Claude Code."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        click.echo(f"Created config: {CONFIG_FILE}")

    claude_settings_path = Path.home() / ".claude" / "settings.json"
    if claude_settings_path.exists():
        settings = json.loads(claude_settings_path.read_text(encoding="utf-8"))
    else:
        claude_settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = {}

    if "mcpServers" not in settings:
        settings["mcpServers"] = {}

    if use_uvx:
        settings["mcpServers"]["engram-ai"] = {
            "command": "uvx",
            "args": ["engram-ai[mcp]"],
        }
    else:
        settings["mcpServers"]["engram-ai"] = {
            "command": "engram-ai",
            "args": ["serve"],
        }

    claude_settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _register_hooks(claude_settings_path)

    click.echo(f"Updated Claude Code settings: {claude_settings_path}")
    click.echo("\nSetup complete. Restart Claude Code to activate Engram-AI.")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/engram_ai/cli.py tests/test_cli.py
git commit -m "feat: add --uvx flag to setup command for uvx-based MCP config"
```

---

### Task 10: Full test suite verification

- [ ] **Step 1: Run all tests**

```bash
cd /f/playground/Engram-AI
pytest --tb=short -q
```

Expected: ALL PASS, no failures

- [ ] **Step 2: Verify core-only import works without extras**

```bash
python -c "
from engram_ai import Forge, Experience, Skill, ProjectManager, QueryResult
from engram_ai.storage import BaseStorage
from engram_ai.llm import BaseLLM
print('All public imports OK')
"
```

Expected: `All public imports OK`

- [ ] **Step 3: Final commit if any cleanup needed**

```bash
git add -A
git commit -m "chore: final cleanup for pip + MCP distribution"
```
