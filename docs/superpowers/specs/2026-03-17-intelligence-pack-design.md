# Engram-AI Intelligence Pack Design Specification

## Overview

Six features that transform Engram-AI from a passive learning system into a proactive intelligence layer. Architecture: Hook-Centric — hooks fire reliably on every interaction, ensuring zero-effort learning and proactive skill injection.

## Feature 1: Active Recall

### Purpose

Proactively inject relevant skills and warnings into Claude's context when the user submits a prompt, so the agent benefits from past learning without needing to query manually.

### Hook Integration

Triggered in `hook user-prompt-submit`, **after** the existing auto-learn cycle (complete_pending + crystallize + evolve).

### Forge Method

```python
def recall(self, context: str, k_skills: int = 3, k_experiences: int = 2) -> dict:
    """Search for relevant skills and negative experiences for a given context.

    Returns:
        {"skills": list[Skill], "warnings": list[Experience]}
        - skills: top k_skills matching active skills (similarity >= 0.4)
        - warnings: top k_experiences negative experiences (valence < -0.3, similarity >= 0.4)
    """
```

### Hook Behavior

- After auto-learn completes, call `forge.recall(user_message)`
- If skills or warnings found, output to stdout: `{"result": "<formatted text>"}`
- If nothing found, output nothing (no empty result)
- Claude Code injects `result` into the conversation context

### Output Format

```
Relevant knowledge:
- Use eager loading for list endpoints (confidence: 0.85)
- Never store session tokens in localStorage (confidence: 0.92)
Past issues in similar context:
- auth middleware change caused test gap in production (valence: -0.8)
```

### Internal Logic

1. `query_skills(context, k=k_skills)` — filter results by `similarity >= 0.4`, keep top `k_skills`
2. `query_experiences(context, k=k_experiences * 3)` — filter by `valence < -0.3` AND `similarity >= 0.4`, keep top `k_experiences`
3. Similarity scores are used internally for filtering and ranking but are not exposed in the return value

### Validation

- Empty user messages: skip recall
- If both `k_skills` and `k_experiences` are 0: return `{"skills": [], "warnings": []}` immediately
- If recall raises an exception: silently ignore (hooks must never block)

---

## Feature 2: Pre-emptive Warning

### Purpose

Monitor agent tool usage in real-time and warn when the current action matches a past failure pattern.

### Hook Integration

Triggered in `hook post-tool-use`, **after** the existing `record_pending`.

### Forge Method

```python
def warn(self, action: str, context: str, threshold: float = 0.6) -> list[Experience]:
    """Search for past negative experiences similar to the current action.

    Returns negative experiences where:
    - valence < -0.3
    - similarity >= threshold
    Sorted by similarity descending.
    """
```

### Internal Logic

1. Combine action and context for richer search: `search_text = f"{action} {context}"`
2. `query_experiences(search_text, k=10)` for similar experiences
3. Filter: `valence < -0.3` AND `similarity >= threshold`
4. Return filtered list sorted by similarity descending (may be empty)

### Hook Behavior

- After `record_pending`, call `forge.warn(action, context)`
- If warnings found, output: `{"result": "<formatted warning>"}`
- If none found, output nothing

### Output Format

```
Warning: past issues with similar actions:
- "CSRF vulnerability after session handling change in auth.py" (valence: -0.8)
```

### Performance

ChromaDB vector search is sub-10ms. No performance concern for hook execution.

---

## Feature 3: Conversational Teaching

### Purpose

Allow users to directly teach skills to Engram-AI without going through the experience cycle. Enables explicit knowledge injection.

### MCP Tool Definition

```json
{
  "name": "engram_teach",
  "inputSchema": {
    "type": "object",
    "properties": {
      "rule": {"type": "string", "description": "The skill/rule to remember"},
      "context_pattern": {"type": "string", "description": "When this applies"},
      "skill_type": {"type": "string", "enum": ["positive", "anti"], "default": "positive"},
      "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.8},
      "project": {"type": "string", "description": "Target project"}
    },
    "required": ["rule", "context_pattern"]
  }
}
```

### Forge Method

```python
def teach(self, rule: str, context_pattern: str,
          skill_type: str = "positive",
          confidence: float = 0.8) -> Skill:
    """Create a skill directly from user instruction.

    - source_experiences=[] (no experience backing)
    - evidence_count=0
    - valence_summary={} (no experience-derived valence data)
    - Validates skill_type in {"positive", "anti"}, raises ValueError otherwise
    - If similar skill exists (similarity >= 0.5): reinforce instead of creating duplicate
    - Emits SKILL_CRYSTALLIZED event
    """
```

### Deduplication

- Before creating, query existing skills: `query_skills(rule, k=3)`
- If any match has similarity >= 0.5:
  - Increment that skill's `confidence` by 0.1 (capped at 1.0)
  - Increment `reinforcement_count`
  - Return the reinforced skill
- Otherwise: create new Skill and store

### Response Format

New skill:
```
Taught: "Always use parameterized queries" (confidence: 0.80)
```

Reinforced existing:
```
Reinforced existing skill: "Use parameterized queries for SQL injection prevention" (confidence: 0.85 -> 0.95)
```

---

## Feature 4: Cross-Project Transfer Learning

### Purpose

High-confidence skills automatically propagate to a global pool, making them available to all projects. Solves the cold-start problem for new projects.

### Storage Layout

```
ProjectManager.base_path/
  _global/              # Global skill pool (new)
    chroma.sqlite3
  project-a/
  project-b/
  default/
```

### Promotion Rules

A skill is eligible for global promotion when:
- `confidence >= 0.9`
- `evidence_count >= 3`

### Promotion Timing

After `crystallize()` returns skills, check all project skills for promotion eligibility. This happens automatically inside `Forge.crystallize()`.

### Forge Method

```python
def promote_to_global(self, skill: Skill) -> Skill:
    """Copy skill to global pool with metadata.source_project set.

    Deduplication: queries global pool with query_skills(skill.rule, k=3).
    If a match with similarity >= 0.7 exists, reinforce it instead of creating duplicate.
    """
```

### Promotion Location

The promotion check is added in `Forge.crystallize()` after calling `self._crystallizer.crystallize()`, not inside the Crystallizer class itself.

### ProjectManager Extensions

```python
def get_global_forge(self) -> Forge:
    """Return Forge for _global pool. Creates if needed."""

def sync_global_skills(self, project: str) -> list[Skill]:
    """Import global skills into project that don't already exist.
    Imported skills get confidence * 0.8 and metadata.imported_from = '_global'.
    Deduplication: skip if similar skill (similarity >= 0.7) already exists in project."""
```

### Sync Timing

- `get_forge(project)` triggers `sync_global_skills(project)` automatically
- Only syncs if global pool has skills not yet seen by this project
- Track sync state via `_global_sync.json` file in the project directory: `{"last_global_sync": "ISO-timestamp"}`

### Special Handling

- `_global` excluded from `list_projects()` (filter by name)
- `delete_project("_global")` raises ValueError
- `_global` already passes the existing `^[a-zA-Z0-9_-]+$` regex — no validation change needed

---

## Feature 5: Feedback Loop Closure

### Purpose

Track whether evolved skills actually improve outcomes. Self-correcting: ineffective skills lose confidence, effective skills gain confidence.

### Skill Model Extension

Add two fields to `Skill`:
```python
prediction_hits: int = 0       # Post-evolve positive outcomes in similar context
prediction_misses: int = 0     # Post-evolve negative outcomes in similar context
```

### Tracking Logic

Called from `Forge.record()` after `self._recorder.record()` returns. The Forge method `check_skill_effectiveness()` performs the tracking — Recorder is not modified.

"Applied" means the skill has been written to a config file (marked by `Evolver.evolve()` via `mark_skills_applied()`). This tracks whether skills that were codified into agent instructions actually lead to better outcomes in similar contexts.

1. Query skills: `query_skills(experience.context, k=5)`
2. Filter: skill has `applied == True` (written to config) AND `similarity >= 0.5`
3. For each matching applied skill:
   - If `experience.valence >= 0.3`: `skill.prediction_hits += 1`
   - If `experience.valence <= -0.3`: `skill.prediction_misses += 1`
   - Update skill in storage

### Automatic Confidence Adjustment

After updating hits/misses, evaluate:
- Hit rate = `hits / (hits + misses)` (only when `hits + misses >= 3`)
- If hit rate **<= 0.3** and `misses >= 3`: `confidence *= 0.7` (skill is not working)
- If hit rate **>= 0.8** and `hits >= 3`: `confidence = min(1.0, confidence + 0.1)` (skill is effective)

### Forge Method

```python
def check_skill_effectiveness(self, experience: Experience) -> list[Skill]:
    """Evaluate applied skills against a new experience.
    Returns skills whose confidence was adjusted."""
```

### Event

New event: `SKILL_EFFECTIVENESS_UPDATED` — emitted when a skill's confidence is adjusted by the feedback loop.

### Integration

- Called automatically inside `Forge.record()` after `self._recorder.record()` returns — Recorder is not modified
- Pure similarity + valence check, no LLM needed
- Uses existing `self._storage.query_skills()` and `self._storage.update_skill()`

---

## Feature 6: Skill Marketplace (Export/Import)

### Purpose

Export skills as shareable packs and import packs from others. Foundation for community skill sharing.

### Pack Format (`.engram-pack.json`)

```json
{
  "format_version": 1,
  "name": "pack-name",
  "description": "Description of this skill pack",
  "exported_at": "2026-03-17T23:00:00Z",
  "source_project": "project-name",
  "skills": [
    {
      "rule": "skill rule text",
      "context_pattern": "when this applies",
      "skill_type": "positive",
      "confidence": 0.92,
      "evidence_count": 5
    }
  ]
}
```

### Forge Methods

```python
def export_skills(self, name: str, description: str = "") -> dict:
    """Export all active skills as a pack dict.
    Only exports active (non-superseded) skills."""

def import_skills(self, pack: dict, confidence_scale: float = 0.8) -> dict:
    """Import skills from a pack.
    Returns: {"imported": list[Skill], "skipped": list[dict], "reinforced": list[Skill]}
    - Skipped: existing skill with similarity >= 0.7
    - Reinforced: existing skill with similarity >= 0.5 (but < 0.7)
    - Imported confidence = original * confidence_scale
    """
```

### CLI Commands

```bash
# Export
engram-ai export --name "react-best-practices" --output ./pack.engram-pack.json
# Options: --project (default from config)

# Import
engram-ai import ./pack.engram-pack.json
# Options: --confidence 0.8, --dry-run, --project
```

### MCP Tools

```json
{"name": "engram_export", "inputSchema": {"name": "string (required)", "description": "string", "project": "string"}}
{"name": "engram_import", "inputSchema": {"path": "string (required)", "confidence_scale": "number (default 0.8)", "project": "string"}}
```

### Implementation Notes

- File I/O (reading/writing `.engram-pack.json`) is handled by the CLI commands. Forge methods work with in-memory dicts only.
- CLI function named `import_pack` with `@main.command("import")` to avoid Python keyword conflict. Similarly `export_pack` with `@main.command("export")`.

### Validation

- `format_version` must be 1; raise `EngramError(f"Unsupported pack format version: {version}")` for unknown versions
- `skills` must be a non-empty list
- Each skill must have `rule` and `context_pattern`
- `skill_type` defaults to "positive" if missing
- `confidence` clamped to [0.0, 1.0]

### Security

- Only skill data is imported (rule, context_pattern, skill_type, confidence, evidence_count)
- No executable code, no experience data, no metadata passthrough
- Unknown fields in skill entries are ignored

---

## Deduplication Thresholds

Three operations add external skills, each with different thresholds:

| Operation | Skip (exact dup) | Reinforce | Rationale |
|-----------|------------------|-----------|-----------|
| `teach()` | — | >= 0.5 | Single user instruction; low bar to merge with existing similar skill |
| `import_skills()` | >= 0.7 | >= 0.5 | Bulk external; higher bar to skip (pack author may have distinct intent) |
| `sync_global_skills()` | >= 0.7 | — | Cross-project; conservative to avoid noise from unrelated projects |
| `promote_to_global()` | >= 0.7 | reinforce | Global pool; avoid duplicates from multiple projects |

## Implementation Order

Features should be implemented in this order due to dependencies:

1. **Feature 5** (Feedback Loop) — Adds `prediction_hits`/`prediction_misses` to Skill model; other features depend on stable model
2. **Feature 3** (Conversational Teaching) — Standalone; establishes the direct-skill-creation pattern reused by Feature 4
3. **Feature 1** (Active Recall) and **Feature 2** (Pre-emptive Warning) — Independent of each other, both hook-based
4. **Feature 4** (Cross-Project Transfer) — Depends on stable Skill model and can reuse teach-like patterns
5. **Feature 6** (Skill Marketplace) — Depends on stable Skill model and export format

---

## Files Changed

| File | Change |
|------|--------|
| `src/engram_ai/forge.py` | Add `recall()`, `warn()`, `teach()`, `promote_to_global()`, `check_skill_effectiveness()`, `export_skills()`, `import_skills()`; modify `record()` to call `check_skill_effectiveness()`; modify `crystallize()` to check promotion eligibility |
| `src/engram_ai/cli.py` | Enhance hooks with recall/warn, add `export`/`import` commands |
| `src/engram_ai/mcp.py` | Add `engram_teach`, `engram_export`, `engram_import` tools |
| `src/engram_ai/project.py` | Add `get_global_forge()`, `sync_global_skills()`, exclude `_global` from list |
| `src/engram_ai/models/skill.py` | Add `prediction_hits`, `prediction_misses` fields |
| `src/engram_ai/events/events.py` | Add `SKILL_EFFECTIVENESS_UPDATED` event |
| `tests/test_forge.py` | Tests for recall, warn, teach, export, import, effectiveness |
| `tests/test_hook_auto_learn.py` | Tests for recall/warn in hooks |
| `tests/test_project.py` | Tests for global pool, sync, promotion |
| `tests/test_mcp.py` | Tests for engram_teach, engram_export, engram_import |
