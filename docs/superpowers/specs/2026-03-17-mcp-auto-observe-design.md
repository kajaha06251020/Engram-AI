# MCP Auto-Observe Design Specification

## Overview

Add an `engram_observe` MCP tool that accepts a conversation snippet, uses LLM to automatically extract recordable experiences, and triggers crystallize when enough experiences accumulate. This removes the need for AI to manually decompose conversations into action/context/outcome/valence fields.

## Feature: `engram_observe` MCP Tool

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "messages": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "role": {"type": "string", "enum": ["user", "assistant"]},
          "content": {"type": "string"}
        },
        "required": ["role", "content"]
      },
      "description": "Conversation history (recent N turns)"
    },
    "max_turns": {
      "type": "integer",
      "description": "Max turn pairs to use from the end of messages",
      "default": 3
    },
    "crystallize_threshold": {
      "type": "integer",
      "description": "Auto-crystallize when total experiences >= this value",
      "default": 5
    }
  },
  "required": ["messages"]
}
```

### Behavior

1. Trim `messages` to the last `max_turns` turn pairs (1 turn = user + assistant). If messages has fewer turns, use all.
2. Call `BaseLLM.extract_experience(trimmed_messages)` to determine if the conversation contains a recordable experience.
3. If LLM returns `None` (no notable experience): respond with `"No notable experience detected."` and stop.
4. If LLM returns an experience dict: call `Forge.record(action, context, outcome, valence)` to persist it.
5. After recording, check if total experience count >= `crystallize_threshold`. If so, run `Forge.crystallize()` automatically.
6. Return a summary including the recorded experience and any crystallized skills.

### Response Examples

**No experience detected:**
```
No notable experience detected.
```

**Experience recorded, no crystallize:**
```
Recorded: "Fixed N+1 query in user API" (valence: 0.80)
```

**Experience recorded + auto-crystallize:**
```
Recorded: "Fixed N+1 query in user API" (valence: 0.80)
Auto-crystallized 2 skill(s):
  - Use eager loading for list endpoints (confidence: 0.85)
  - Add query count assertions in API tests (confidence: 0.72)
```

## BaseLLM Interface Extension

Add one method to `BaseLLM`:

```python
def extract_experience(self, messages: list[dict]) -> dict | None:
    """Extract a recordable experience from a conversation snippet.

    Args:
        messages: List of {"role": "user"|"assistant", "content": str}

    Returns:
        {"action": str, "context": str, "outcome": str, "valence": float}
        or None if no notable experience found.
    """
```

- Default implementation raises `NotImplementedError` (backward-compatible with v0.2 pattern).
- `ClaudeLLM`: sends conversation to Anthropic API with a system prompt instructing it to extract experiences (technical learnings, failure lessons, success patterns) or return null for casual/question-only conversations.
- `MockLLM` (test fixture): returns a canned experience dict for messages containing specific keywords, `None` otherwise.

### ClaudeLLM Prompt Strategy

The system prompt instructs the LLM to:
- Look for technical learnings, failure lessons, success patterns, or important caveats in the conversation
- Skip casual chat, pure questions without resolution, or trivial exchanges
- Return a JSON object with `action`, `context`, `outcome`, `valence` fields
- Derive `valence` from the conversation tone and outcome (-1.0 to 1.0)

## Forge Extension

### New Method: `observe()`

```python
def observe(self, messages: list[dict], max_turns: int = 3,
            crystallize_threshold: int = 5) -> dict:
```

**Returns:** `{"recorded": Experience | None, "crystallized": list[Skill]}`

### Message Trimming

Private utility `_trim_messages(messages, max_turns)`:
- 1 turn = 1 user message + 1 assistant message pair
- Takes the last `max_turns` pairs from the end of `messages`
- If fewer turns exist, returns all messages

### Crystallize Trigger Logic

After recording an experience:
- Count total experiences via `self._storage.get_all_experiences()`
- If count >= `crystallize_threshold`, run `self.crystallize()`
- Otherwise skip (saves LLM cost)

## Files Changed

| File | Change |
|------|--------|
| `src/engram_ai/llm/base.py` | Add `extract_experience` with `NotImplementedError` default |
| `src/engram_ai/llm/claude.py` | Implement `extract_experience` with Anthropic API |
| `src/engram_ai/forge.py` | Add `observe()` + `_trim_messages()` |
| `src/engram_ai/mcp.py` | Add `engram_observe` tool definition and handler |
| `tests/conftest.py` | Add `extract_experience` to `MockLLM` |
| `tests/llm/test_extract.py` | New: unit tests for extract_experience |
| `tests/test_mcp.py` | Add engram_observe tool tests |
| `tests/test_forge.py` | New: Forge.observe() tests |
