# MCP Auto-Observe Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `engram_observe` MCP tool that auto-extracts experiences from conversation snippets via LLM and auto-triggers crystallize at configurable thresholds.

**Architecture:** Extend 4 layers bottom-up: LLM interface (`extract_experience`) → Forge facade (`observe()` + `_trim_messages()`) → MCP tool (`engram_observe`). TDD throughout.

**Tech Stack:** Python 3.10+, Pydantic 2, Anthropic SDK, MCP server, pytest

**Spec:** `docs/superpowers/specs/2026-03-17-mcp-auto-observe-design.md`

**Baseline:** 121 tests passing (excluding dashboard). Run `pytest tests/ --ignore=tests/dashboard -q` to verify.

---

## Chunk 1: LLM Layer — `extract_experience`

### Task 1: BaseLLM Interface — Add `extract_experience`

**Files:**
- Modify: `src/engram_ai/llm/base.py`

- [ ] **Step 1: Add `extract_experience` method with NotImplementedError default**

```python
# Append after merge_skills method in BaseLLM class

    def extract_experience(self, messages: list[dict]) -> dict | None:
        """Extract a recordable experience from a conversation snippet.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}

        Returns:
            {"action": str, "context": str, "outcome": str, "valence": float}
            or None if no notable experience found.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support extract_experience. "
            "Upgrade your LLM implementation."
        )
```

- [ ] **Step 2: Run full suite to check no regressions**

Run: `pytest tests/ --ignore=tests/dashboard -q`
Expected: ALL PASS (121)

- [ ] **Step 3: Commit**

```bash
git add src/engram_ai/llm/base.py
git commit -m "feat(llm): add extract_experience to BaseLLM interface"
```

### Task 2: MockLLM — Add `extract_experience` for tests

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add extract_experience support to MockLLM**

```python
# In MockLLM.__init__, add:
        self._extract_experience_response = None

# Add setter method:
    def set_extract_experience_response(self, response: dict | None):
        self._extract_experience_response = response

# Add method:
    def extract_experience(self, messages: list[dict]) -> dict | None:
        return self._extract_experience_response
```

- [ ] **Step 2: Run full suite to check no regressions**

Run: `pytest tests/ --ignore=tests/dashboard -q`
Expected: ALL PASS (121)

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add extract_experience to MockLLM"
```

### Task 3: ClaudeLLM — Implement `extract_experience`

**Files:**
- Create: `tests/llm/test_extract.py`
- Modify: `src/engram_ai/llm/claude.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/llm/test_extract.py
import json
import pytest
from unittest.mock import MagicMock, patch
from engram_ai.llm.claude import ClaudeLLM


@pytest.fixture
def claude_llm():
    with patch("engram_ai.llm.claude.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        llm = ClaudeLLM(api_key="test-key")
        llm._client = mock_client
        yield llm


def test_extract_experience_returns_dict(claude_llm):
    """LLM returns a valid experience dict."""
    response_json = json.dumps({
        "action": "Fixed N+1 query",
        "context": "User API endpoint was slow",
        "outcome": "Response time improved 10x",
        "valence": 0.9,
    })
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_json)]
    claude_llm._client.messages.create.return_value = mock_response

    result = claude_llm.extract_experience([
        {"role": "user", "content": "The API is slow"},
        {"role": "assistant", "content": "I fixed the N+1 query"},
    ])
    assert result is not None
    assert result["action"] == "Fixed N+1 query"
    assert result["valence"] == 0.9


def test_extract_experience_returns_none_for_no_experience(claude_llm):
    """LLM returns null when no notable experience."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"experience": null}')]
    claude_llm._client.messages.create.return_value = mock_response

    result = claude_llm.extract_experience([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ])
    assert result is None


def test_extract_experience_clamps_valence(claude_llm):
    """Valence is clamped to [-1.0, 1.0]."""
    response_json = json.dumps({
        "action": "a", "context": "c", "outcome": "o", "valence": 5.0,
    })
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_json)]
    claude_llm._client.messages.create.return_value = mock_response

    result = claude_llm.extract_experience([{"role": "user", "content": "x"}])
    assert result["valence"] == 1.0


def test_extract_experience_returns_none_on_malformed_json(claude_llm):
    """Malformed JSON returns None."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="not json")]
    claude_llm._client.messages.create.return_value = mock_response

    result = claude_llm.extract_experience([{"role": "user", "content": "x"}])
    assert result is None


def test_extract_experience_returns_none_on_missing_keys(claude_llm):
    """JSON with missing required keys returns None."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"action": "a"}')]
    claude_llm._client.messages.create.return_value = mock_response

    result = claude_llm.extract_experience([{"role": "user", "content": "x"}])
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/llm/test_extract.py -v`
Expected: FAIL — `extract_experience` raises `NotImplementedError`

- [ ] **Step 3: Implement `extract_experience` in ClaudeLLM**

```python
# Append to ClaudeLLM class in src/engram_ai/llm/claude.py

    def extract_experience(self, messages: list[dict]) -> dict | None:
        system = (
            "You analyze conversations between a user and an AI assistant to extract "
            "notable experiences worth recording for future learning.\n\n"
            "Look for: technical learnings, failure lessons, success patterns, "
            "debugging insights, or important caveats.\n"
            "Skip: casual chat, greetings, pure questions without resolution, "
            "trivial exchanges.\n\n"
            "If the conversation contains a recordable experience, respond with ONLY "
            "a JSON object:\n"
            '{"action": "<what was done>", "context": "<situation/problem>", '
            '"outcome": "<what happened/result>", "valence": <float from -1.0 to 1.0>}\n\n'
            "If there is no notable experience, respond with ONLY:\n"
            '{"experience": null}'
        )
        transcript = "\n".join(
            f"[{m['role']}]: {m['content']}" for m in messages
        )
        result = self._call(system, transcript)
        try:
            parsed = json.loads(result)
            if parsed.get("experience") is None and "action" not in parsed:
                return None
            required = ("action", "context", "outcome", "valence")
            if not all(k in parsed for k in required):
                return None
            parsed["valence"] = max(-1.0, min(1.0, float(parsed["valence"])))
            return {k: parsed[k] for k in required}
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning("Failed to parse extract_experience response: %s", e)
            return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/llm/test_extract.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run full suite to check no regressions**

Run: `pytest tests/ --ignore=tests/dashboard -q`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/engram_ai/llm/claude.py tests/llm/test_extract.py
git commit -m "feat(llm): implement extract_experience in ClaudeLLM"
```

---

## Chunk 2: Forge Layer — `observe()` + `_trim_messages()`

### Task 4: Forge.observe() — Tests

**Files:**
- Create: `tests/test_forge.py`

- [ ] **Step 1: Write failing tests for observe() and _trim_messages()**

```python
# tests/test_forge.py
import pytest
from engram_ai.forge import Forge, _trim_messages
from engram_ai.exceptions import EngramError
from tests.conftest import MockLLM


@pytest.fixture
def forge_with_mock(tmp_path):
    llm = MockLLM()
    forge = Forge(storage_path=str(tmp_path / "data"), llm=llm)
    return forge, llm


# --- _trim_messages tests ---

def test_trim_messages_default():
    msgs = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
        {"role": "assistant", "content": "d"},
        {"role": "user", "content": "e"},
        {"role": "assistant", "content": "f"},
    ]
    result = _trim_messages(msgs, max_turns=2)
    assert len(result) == 4
    assert result[0]["content"] == "c"


def test_trim_messages_fewer_than_max():
    msgs = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    result = _trim_messages(msgs, max_turns=5)
    assert len(result) == 2


def test_trim_messages_strips_empty_content():
    msgs = [
        {"role": "user", "content": ""},
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    result = _trim_messages(msgs, max_turns=3)
    assert len(result) == 2
    assert result[0]["content"] == "a"


def test_trim_messages_strips_system_role():
    msgs = [
        {"role": "system", "content": "you are helpful"},
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    result = _trim_messages(msgs, max_turns=3)
    assert len(result) == 2
    assert all(m["role"] in ("user", "assistant") for m in result)


def test_trim_messages_empty_list():
    assert _trim_messages([], max_turns=3) == []


# --- observe() tests ---

def test_observe_records_experience(forge_with_mock):
    forge, llm = forge_with_mock
    llm.set_extract_experience_response({
        "action": "Fixed bug",
        "context": "Login page broken",
        "outcome": "Users can log in",
        "valence": 0.8,
    })
    result = forge.observe([
        {"role": "user", "content": "Login is broken"},
        {"role": "assistant", "content": "I fixed the auth bug"},
    ])
    assert result["recorded"] is not None
    assert result["recorded"].action == "Fixed bug"
    assert result["crystallized"] == []


def test_observe_returns_none_when_no_experience(forge_with_mock):
    forge, llm = forge_with_mock
    llm.set_extract_experience_response(None)
    result = forge.observe([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ])
    assert result["recorded"] is None
    assert result["crystallized"] == []


def test_observe_empty_messages(forge_with_mock):
    forge, llm = forge_with_mock
    result = forge.observe([])
    assert result["recorded"] is None
    assert result["crystallized"] == []


def test_observe_auto_crystallize_at_threshold(forge_with_mock):
    forge, llm = forge_with_mock
    # Pre-fill 4 experiences
    for i in range(4):
        forge.record(action=f"action{i}", context=f"ctx{i}",
                     outcome=f"out{i}", valence=0.5)

    # The 5th triggers crystallize (5 % 5 == 0)
    llm.set_extract_experience_response({
        "action": "action4", "context": "ctx4",
        "outcome": "out4", "valence": 0.7,
    })
    # MockLLM.crystallize_pattern returns None by default, so crystallized=[]
    result = forge.observe(
        [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}],
        crystallize_threshold=5,
    )
    assert result["recorded"] is not None
    # crystallize was called (no error), returned empty since MockLLM returns None
    assert result["crystallized"] == []


def test_observe_no_crystallize_below_threshold(forge_with_mock):
    forge, llm = forge_with_mock
    llm.set_extract_experience_response({
        "action": "a", "context": "c", "outcome": "o", "valence": 0.5,
    })
    result = forge.observe(
        [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}],
        crystallize_threshold=5,
    )
    assert result["recorded"] is not None
    assert result["crystallized"] == []


def test_observe_rejects_low_threshold(forge_with_mock):
    forge, llm = forge_with_mock
    with pytest.raises(EngramError, match="crystallize_threshold"):
        forge.observe([{"role": "user", "content": "x"}], crystallize_threshold=1)


def test_observe_raises_on_unsupported_llm(tmp_path):
    from engram_ai.llm.base import BaseLLM
    from engram_ai.models.experience import Experience
    from engram_ai.models.skill import Skill

    class MinimalLLM(BaseLLM):
        def detect_valence(self, msg): return 0.0
        def crystallize_pattern(self, exps): return None
        def generate_evolution_text(self, skills): return ""

    forge = Forge(storage_path=str(tmp_path / "data"), llm=MinimalLLM())
    with pytest.raises(EngramError, match="extract_experience"):
        forge.observe([{"role": "user", "content": "x"}])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_forge.py -v`
Expected: FAIL — `_trim_messages` and `observe()` don't exist yet

### Task 5: Forge.observe() — Implementation

**Files:**
- Modify: `src/engram_ai/forge.py`

- [ ] **Step 1: Add `_trim_messages` utility function**

```python
# Add at module level in forge.py, after imports

def _trim_messages(messages: list[dict], max_turns: int = 3) -> list[dict]:
    """Trim messages to the last max_turns turn pairs.

    Strips empty content and non-user/assistant roles, then takes
    the last max_turns*2 messages.
    """
    filtered = [
        m for m in messages
        if m.get("role") in ("user", "assistant") and m.get("content", "").strip()
    ]
    limit = max_turns * 2
    if len(filtered) <= limit:
        return filtered
    return filtered[-limit:]
```

- [ ] **Step 2: Add `observe()` method to Forge class**

```python
# Add to Forge class, after detect_valence method

    def observe(self, messages: list[dict], max_turns: int = 3,
                crystallize_threshold: int = 5) -> dict:
        """Observe a conversation snippet and auto-record/crystallize."""
        if crystallize_threshold < 2:
            raise EngramError("crystallize_threshold must be >= 2")

        trimmed = _trim_messages(messages, max_turns)
        if not trimmed:
            return {"recorded": None, "crystallized": []}

        try:
            extracted = self._llm.extract_experience(trimmed)
        except NotImplementedError:
            raise EngramError(
                "observe requires an LLM that supports extract_experience"
            )

        if extracted is None:
            return {"recorded": None, "crystallized": []}

        exp = self.record(
            action=extracted["action"],
            context=extracted["context"],
            outcome=extracted["outcome"],
            valence=extracted["valence"],
        )

        crystallized = []
        count = len(self._storage.get_all_experiences())
        if count >= crystallize_threshold and count % crystallize_threshold == 0:
            crystallized = self.crystallize()

        return {"recorded": exp, "crystallized": crystallized}
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `pytest tests/test_forge.py -v`
Expected: ALL PASS

- [ ] **Step 4: Run full suite to check no regressions**

Run: `pytest tests/ --ignore=tests/dashboard -q`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_forge.py src/engram_ai/forge.py
git commit -m "feat(forge): add observe() with auto-record and crystallize trigger"
```

---

## Chunk 3: MCP Layer — `engram_observe` tool

### Task 6: MCP Tool — Tests

**Files:**
- Modify: `tests/test_mcp.py`

- [ ] **Step 1: Write failing tests for engram_observe**

```python
# Append to tests/test_mcp.py

@pytest.mark.asyncio
async def test_list_tools_includes_observe(forge_and_server):
    _, server = forge_and_server
    tools = await _list_tools(server)
    tool_names = [t.name for t in tools]
    assert "engram_observe" in tool_names


@pytest.mark.asyncio
async def test_engram_observe_no_experience(forge_and_server):
    forge, server = forge_and_server
    result = await _call_tool(server, "engram_observe", {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
    })
    assert "No notable experience" in result[0].text


@pytest.mark.asyncio
async def test_engram_observe_records(forge_and_server):
    forge, server = forge_and_server
    # Configure MockLLM to return an experience
    forge._llm.set_extract_experience_response({
        "action": "Fixed auth bug",
        "context": "Login was broken",
        "outcome": "Login works now",
        "valence": 0.9,
    })
    result = await _call_tool(server, "engram_observe", {
        "messages": [
            {"role": "user", "content": "Login is broken"},
            {"role": "assistant", "content": "Fixed the auth middleware"},
        ],
    })
    assert "Recorded" in result[0].text
    assert "Fixed auth bug" in result[0].text


@pytest.mark.asyncio
async def test_engram_observe_empty_messages(forge_and_server):
    _, server = forge_and_server
    result = await _call_tool(server, "engram_observe", {"messages": []})
    assert "No notable experience" in result[0].text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_mcp.py::test_list_tools_includes_observe tests/test_mcp.py::test_engram_observe_no_experience -v`
Expected: FAIL — `engram_observe` tool not registered yet

### Task 7: MCP Tool — Implementation

**Files:**
- Modify: `src/engram_ai/mcp.py`

- [ ] **Step 1: Add `engram_observe` to tool list**

```python
# Add to the list_tools() return list, after engram_decay Tool

            Tool(
                name="engram_observe",
                description="Observe a conversation snippet and auto-record experiences",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant"]},
                                    "content": {"type": "string"},
                                },
                                "required": ["role", "content"],
                            },
                            "description": "Conversation history",
                        },
                        "max_turns": {
                            "type": "integer",
                            "description": "Max turn pairs to use",
                            "default": 3,
                            "minimum": 1,
                        },
                        "crystallize_threshold": {
                            "type": "integer",
                            "description": "Auto-crystallize every N experiences",
                            "default": 5,
                            "minimum": 2,
                        },
                    },
                    "required": ["messages"],
                },
            ),
```

- [ ] **Step 2: Add `engram_observe` handler**

```python
# Add to call_tool() handler, before the else clause

            elif name == "engram_observe":
                result = forge.observe(
                    messages=arguments["messages"],
                    max_turns=arguments.get("max_turns", 3),
                    crystallize_threshold=arguments.get("crystallize_threshold", 5),
                )
                if result["recorded"] is None:
                    return [TextContent(type="text", text="No notable experience detected.")]
                lines = [f'Recorded: "{result["recorded"].action}" (valence: {result["recorded"].valence:.2f})']
                if result["crystallized"]:
                    lines.append(f"Auto-crystallized {len(result['crystallized'])} skill(s):")
                    for s in result["crystallized"]:
                        lines.append(f"  - {s.rule} (confidence: {s.confidence:.2f})")
                return [TextContent(type="text", text="\n".join(lines))]
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `pytest tests/test_mcp.py -v`
Expected: ALL PASS

- [ ] **Step 4: Run full suite to check no regressions**

Run: `pytest tests/ --ignore=tests/dashboard -q`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/engram_ai/mcp.py tests/test_mcp.py
git commit -m "feat(mcp): add engram_observe tool with auto-record and crystallize"
```

---

## Chunk 4: Integration Verification

### Task 8: Full Integration Test

**Files:**
- Modify: `tests/integration/test_full_flow.py`

- [ ] **Step 1: Add integration test for observe flow**

```python
# Append to tests/integration/test_full_flow.py

def test_observe_full_flow(tmp_path):
    """End-to-end: observe → auto-record → auto-crystallize."""
    from engram_ai.forge import Forge
    from engram_ai.models.skill import Skill
    from tests.conftest import MockLLM

    llm = MockLLM()
    forge = Forge(storage_path=str(tmp_path / "data"), llm=llm)

    # Pre-fill experiences to reach threshold - 1
    for i in range(4):
        forge.record(action=f"action{i}", context="similar context",
                     outcome=f"outcome{i}", valence=0.7)

    # Set up MockLLM for observe + crystallize
    llm.set_extract_experience_response({
        "action": "optimized query",
        "context": "similar context",
        "outcome": "faster response",
        "valence": 0.9,
    })
    # Provide multiple copies to handle potential multi-cluster scenarios
    optimize_skill = Skill(
        rule="Optimize DB queries for list endpoints",
        context_pattern="API performance",
        confidence=0.85, source_experiences=[], evidence_count=5,
        valence_summary={"positive": 5, "negative": 0},
    )
    llm.set_crystallize_response([optimize_skill] * 3)

    result = forge.observe(
        messages=[
            {"role": "user", "content": "The list endpoint is slow"},
            {"role": "assistant", "content": "I optimized the query with eager loading"},
            {"role": "user", "content": "Perfect, much faster now"},
            {"role": "assistant", "content": "Glad it worked!"},
        ],
        max_turns=2,
        crystallize_threshold=5,
    )

    assert result["recorded"] is not None
    assert result["recorded"].action == "optimized query"
    assert len(result["crystallized"]) >= 1
    assert "Optimize DB queries" in result["crystallized"][0].rule


def test_observe_full_flow_no_crystallize_below_threshold(tmp_path):
    """observe does NOT crystallize when below threshold."""
    from engram_ai.forge import Forge
    from tests.conftest import MockLLM

    llm = MockLLM()
    forge = Forge(storage_path=str(tmp_path / "data"), llm=llm)

    llm.set_extract_experience_response({
        "action": "small fix", "context": "minor issue",
        "outcome": "resolved", "valence": 0.5,
    })
    result = forge.observe(
        messages=[{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}],
        crystallize_threshold=5,
    )
    assert result["recorded"] is not None
    assert result["crystallized"] == []
```

- [ ] **Step 2: Add `extract_experience` to `IntegrationMockLLM` for forward compatibility**

```python
# In tests/integration/test_full_flow.py, add to IntegrationMockLLM class:

    def extract_experience(self, messages):
        return None  # Conservative default
```

- [ ] **Step 3: Run integration test**

Run: `pytest tests/integration/test_full_flow.py::test_observe_full_flow -v`
Expected: PASS

- [ ] **Step 4: Run full suite**

Run: `pytest tests/ --ignore=tests/dashboard -q`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_full_flow.py
git commit -m "test: add observe full flow integration test"
```
