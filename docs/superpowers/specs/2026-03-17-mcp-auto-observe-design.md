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
      "default": 3,
      "minimum": 1
    },
    "crystallize_threshold": {
      "type": "integer",
      "description": "Auto-crystallize every N new experiences since last crystallize",
      "default": 5,
      "minimum": 2
    }
  },
  "required": ["messages"]
}
```

### Validation

- If `messages` is empty or contains no content, return `"No notable experience detected."` immediately without calling the LLM.
- Messages with empty `content` strings are stripped before processing.
- Only `"user"` and `"assistant"` roles are kept; other roles (e.g., `"system"`) are stripped.

### Behavior

1. Validate and trim `messages` to the last `max_turns` turn pairs (see Validation and Message Trimming sections).
2. Call `BaseLLM.extract_experience(trimmed_messages)` to determine if the conversation contains a recordable experience.
3. If LLM returns `None` (no notable experience): respond with `"No notable experience detected."` and stop.
4. If LLM returns an experience dict: call `Forge.record(action, context, outcome, valence)` to persist it.
5. After recording, check crystallize trigger condition (see Crystallize Trigger Logic). If triggered, run `Forge.crystallize()` automatically.
6. The MCP handler formats the `Forge.observe()` return dict into human-readable text following the response examples below.

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

- Default implementation raises `NotImplementedError` (backward-compatible with v0.2 pattern, matching `verify_conflict`/`merge_skills`).
- `ClaudeLLM`: sends conversation to Anthropic API with a system prompt instructing it to extract experiences or return null.
- `MockLLM` (test fixture): returns a canned experience dict for messages containing specific keywords, `None` otherwise.

### Error Handling

- If `extract_experience()` raises `LLMError`, `Forge.observe()` propagates it to the MCP layer, which catches it via the existing top-level `except Exception` handler. This matches the existing pattern for all other MCP tools.
- If `extract_experience()` raises `NotImplementedError` (LLM backend doesn't support it), `Forge.observe()` raises `EngramError("observe requires an LLM that supports extract_experience")`. This matches the existing `merge_skills` guard pattern in Forge.

### ClaudeLLM Implementation

**System prompt (draft):**

```
You analyze conversations between a user and an AI assistant to extract notable experiences worth recording for future learning.

Look for: technical learnings, failure lessons, success patterns, debugging insights, or important caveats.
Skip: casual chat, greetings, pure questions without resolution, trivial exchanges.

If the conversation contains a recordable experience, respond with ONLY a JSON object:
{"action": "<what was done>", "context": "<situation/problem>", "outcome": "<what happened/result>", "valence": <float from -1.0 to 1.0>}

If there is no notable experience, respond with ONLY:
{"experience": null}
```

**Conversation is passed as a formatted transcript in the user message:**
```
[user]: How do I fix the N+1 query?
[assistant]: Use eager loading with select_related()...
```

**Response parsing:**
- Parse JSON response. If `json.JSONDecodeError` or missing keys, log warning and return `None`.
- Clamp `valence` to [-1.0, 1.0].
- If response contains `"experience": null`, return `None`.

## Forge Extension

### New Method: `observe()`

```python
def observe(self, messages: list[dict], max_turns: int = 3,
            crystallize_threshold: int = 5) -> dict:
```

**Returns:** `{"recorded": Experience | None, "crystallized": list[Skill]}`

**Guard:** If `self._llm` does not support `extract_experience` (raises `NotImplementedError`), raise `EngramError("observe requires an LLM that supports extract_experience")`.

### Message Trimming

Private utility `_trim_messages(messages, max_turns)`:
- Strip messages with empty `content` or roles other than `"user"`/`"assistant"`
- Take the last `max_turns * 2` messages from the filtered list (simple slice, no pairing logic)
- If fewer messages exist, return all

This simple approach avoids complex pairing logic for edge cases like consecutive same-role messages or trailing user messages.

### Crystallize Trigger Logic

After recording an experience, crystallize triggers based on a **modulo check** to avoid re-triggering on every call after the threshold is first reached:

```python
count = len(self._storage.get_all_experiences())
if count >= crystallize_threshold and count % crystallize_threshold == 0:
    skills = self.crystallize()
```

This means crystallize runs at experience counts 5, 10, 15, 20... (for threshold=5), not on every call after 5. No state tracking needed.

**Concurrency note:** The MCP server runs single-threaded on stdio. Concurrent crystallize is not a concern for the current architecture. If the server is later made concurrent, a lock should be added.

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
