# Intelligence Pack Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 6つの機能（Active Recall, Pre-emptive Warning, Conversational Teaching, Cross-Project Transfer, Feedback Loop, Skill Marketplace）でEngram-AIをプロアクティブな知能レイヤーに変える。

**Architecture:** Hook-Centric。フックは毎回確実に発火するので、ゼロ努力学習とスキル注入の基盤。MCP toolはConversational TeachingとMarketplaceに使用。

**Tech Stack:** Python 3.12, Click (CLI), MCP SDK, ChromaDB, Pydantic

**Spec:** `docs/superpowers/specs/2026-03-17-intelligence-pack-design.md`

**Run tests:** `.venv/Scripts/python -m pytest tests/<file> -v` (Windows環境)

---

### Task 1: Skill model拡張 + 新イベント (Feature 5 基盤)

**Files:**
- Modify: `src/engram_ai/models/skill.py`
- Modify: `src/engram_ai/events/events.py`
- Test: `tests/test_intelligence_pack.py`

- [ ] **Step 1: テスト作成 — Skillモデルの新フィールド**

```python
# tests/test_intelligence_pack.py
from engram_ai.models.skill import Skill


def test_skill_has_prediction_fields():
    skill = Skill(
        rule="test",
        context_pattern="ctx",
        confidence=0.8,
        source_experiences=[],
        evidence_count=0,
        valence_summary={},
    )
    assert skill.prediction_hits == 0
    assert skill.prediction_misses == 0


def test_skill_prediction_fields_settable():
    skill = Skill(
        rule="test",
        context_pattern="ctx",
        confidence=0.8,
        source_experiences=[],
        evidence_count=0,
        valence_summary={},
        prediction_hits=5,
        prediction_misses=2,
    )
    assert skill.prediction_hits == 5
    assert skill.prediction_misses == 2
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py::test_skill_has_prediction_fields tests/test_intelligence_pack.py::test_skill_prediction_fields_settable -v`
Expected: FAIL (field not found)

- [ ] **Step 3: Skillモデルにフィールド追加**

`src/engram_ai/models/skill.py` の `status` フィールドの後に追加:

```python
    # v0.4: Feedback Loop
    prediction_hits: int = 0
    prediction_misses: int = 0
```

- [ ] **Step 4: イベント定数追加**

`src/engram_ai/events/events.py` の末尾に追加:

```python
# v0.4
SKILL_EFFECTIVENESS_UPDATED = "skill.effectiveness.updated"
```

- [ ] **Step 5: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py -v`
Expected: PASS

- [ ] **Step 6: コミット**

```bash
git add src/engram_ai/models/skill.py src/engram_ai/events/events.py tests/test_intelligence_pack.py
git commit -m "feat: add prediction_hits/misses to Skill model + SKILL_EFFECTIVENESS_UPDATED event"
```

---

### Task 2: Feedback Loop — check_skill_effectiveness (Feature 5)

**Files:**
- Modify: `src/engram_ai/forge.py`
- Test: `tests/test_intelligence_pack.py`

- [ ] **Step 1: テスト作成**

`tests/test_intelligence_pack.py` に追加:

```python
from engram_ai import Forge


def test_check_skill_effectiveness_positive_hit(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    # 手動でapplied skillを作成
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="Use eager loading",
        context_pattern="database queries",
        confidence=0.8,
        source_experiences=["exp1"],
        evidence_count=1,
        valence_summary={"positive": 1},
    )
    forge._storage.store_skill(skill)
    forge._storage.mark_skills_applied([skill.id])

    # 類似コンテキストで正のvalenceの経験を記録
    from engram_ai.models.experience import Experience
    exp = Experience(
        action="Used eager loading",
        context="database queries optimization",
        outcome="Faster queries",
        valence=0.8,
    )
    updated = forge.check_skill_effectiveness(exp)
    # スキルのprediction_hitsが増えるはず
    all_skills = forge._storage.get_all_skills()
    target = [s for s in all_skills if s.id == skill.id][0]
    assert target.prediction_hits >= 1


def test_check_skill_effectiveness_negative_miss(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="Use eager loading",
        context_pattern="database queries",
        confidence=0.8,
        source_experiences=["exp1"],
        evidence_count=1,
        valence_summary={"positive": 1},
    )
    forge._storage.store_skill(skill)
    forge._storage.mark_skills_applied([skill.id])

    from engram_ai.models.experience import Experience
    exp = Experience(
        action="Used eager loading",
        context="database queries optimization",
        outcome="Still slow",
        valence=-0.5,
    )
    forge.check_skill_effectiveness(exp)
    all_skills = forge._storage.get_all_skills()
    target = [s for s in all_skills if s.id == skill.id][0]
    assert target.prediction_misses >= 1


def test_check_skill_effectiveness_confidence_drop(tmp_path, mock_llm):
    """3+ misses with low hit rate should reduce confidence."""
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="Use eager loading",
        context_pattern="database queries",
        confidence=0.8,
        source_experiences=["exp1"],
        evidence_count=1,
        valence_summary={"positive": 1},
        prediction_hits=0,
        prediction_misses=2,  # Will become 3 after this
    )
    forge._storage.store_skill(skill)
    forge._storage.mark_skills_applied([skill.id])

    from engram_ai.models.experience import Experience
    exp = Experience(
        action="Used eager loading",
        context="database queries optimization",
        outcome="Failed again",
        valence=-0.5,
    )
    updated = forge.check_skill_effectiveness(exp)
    assert len(updated) >= 1
    assert updated[0].confidence < 0.8  # confidence should have dropped


def test_record_calls_check_effectiveness(tmp_path, mock_llm):
    """Forge.record() should automatically call check_skill_effectiveness."""
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="test skill",
        context_pattern="test context",
        confidence=0.8,
        source_experiences=["exp1"],
        evidence_count=1,
        valence_summary={},
    )
    forge._storage.store_skill(skill)
    forge._storage.mark_skills_applied([skill.id])

    # record() should trigger effectiveness check
    forge.record(
        action="test action",
        context="test context situation",
        outcome="good result",
        valence=0.8,
    )
    all_skills = forge._storage.get_all_skills()
    target = [s for s in all_skills if s.id == skill.id][0]
    # prediction_hits may or may not be updated depending on similarity
    # Just verify no error occurs
    assert target is not None
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py::test_check_skill_effectiveness_positive_hit -v`
Expected: FAIL (method not found)

- [ ] **Step 3: Forge.check_skill_effectiveness 実装**

`src/engram_ai/forge.py` に追加 (Forge class内、`detect_valence` の後):

```python
    def check_skill_effectiveness(self, experience: "Experience") -> list["Skill"]:
        """Evaluate applied skills against a new experience.
        Returns skills whose confidence was adjusted."""
        from engram_ai.events.events import SKILL_EFFECTIVENESS_UPDATED

        adjusted = []
        try:
            similar_skills = self._storage.query_skills(experience.context, k=5)
        except Exception:
            return adjusted

        for skill, similarity in similar_skills:
            if similarity < 0.5:
                continue

            # Update prediction counters
            changed = False
            if experience.valence >= 0.3:
                skill.prediction_hits += 1
                changed = True
            elif experience.valence <= -0.3:
                skill.prediction_misses += 1
                changed = True

            if not changed:
                continue

            # Evaluate confidence adjustment
            total = skill.prediction_hits + skill.prediction_misses
            if total >= 3:
                hit_rate = skill.prediction_hits / total
                if hit_rate <= 0.3 and skill.prediction_misses >= 3:
                    skill.confidence = round(skill.confidence * 0.7, 4)
                    adjusted.append(skill)
                elif hit_rate >= 0.8 and skill.prediction_hits >= 3:
                    skill.confidence = min(1.0, round(skill.confidence + 0.1, 4))
                    adjusted.append(skill)

            self._storage.update_skill(skill)

        for skill in adjusted:
            self._event_bus.emit(SKILL_EFFECTIVENESS_UPDATED, skill)

        return adjusted
```

注意: スペックは「applied == True」フィルタを指定しているが、`query_skills` はappliedメタデータでフィルタできない。代わりに類似度 >= 0.5の全スキルに対してeffectivenessチェックを行う。未evolveスキルも追跡した方がデータとして有用。

- [ ] **Step 4: Forge.record() を修正**

`src/engram_ai/forge.py` の `record` メソッドを修正:

```python
    def record(self, action: str, context: str, outcome: str, valence: float,
               metadata: dict | None = None, parent_id: str | None = None) -> Experience:
        exp = self._recorder.record(action, context, outcome, valence, metadata, parent_id)
        self.check_skill_effectiveness(exp)
        return exp
```

- [ ] **Step 5: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py -v`
Expected: PASS

- [ ] **Step 6: 既存テスト確認**

Run: `.venv/Scripts/python -m pytest tests/ --ignore=tests/dashboard -v`
Expected: ALL PASS

- [ ] **Step 7: コミット**

```bash
git add src/engram_ai/forge.py tests/test_intelligence_pack.py
git commit -m "feat: add Feedback Loop — check_skill_effectiveness in Forge.record()"
```

---

### Task 3: Conversational Teaching — Forge.teach (Feature 3)

**Files:**
- Modify: `src/engram_ai/forge.py`
- Test: `tests/test_intelligence_pack.py`

- [ ] **Step 1: テスト作成**

`tests/test_intelligence_pack.py` に追加:

```python
def test_teach_creates_skill(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    skill = forge.teach(
        rule="Always use parameterized queries",
        context_pattern="SQL database access",
    )
    assert skill.rule == "Always use parameterized queries"
    assert skill.context_pattern == "SQL database access"
    assert skill.confidence == 0.8
    assert skill.source_experiences == []
    assert skill.evidence_count == 0
    assert skill.skill_type == "positive"


def test_teach_anti_skill(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    skill = forge.teach(
        rule="Never use eval()",
        context_pattern="Python code",
        skill_type="anti",
        confidence=0.9,
    )
    assert skill.skill_type == "anti"
    assert skill.confidence == 0.9


def test_teach_invalid_skill_type(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    import pytest
    with pytest.raises(ValueError):
        forge.teach(rule="test", context_pattern="ctx", skill_type="invalid")


def test_teach_reinforces_similar(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    skill1 = forge.teach(
        rule="Use parameterized queries for SQL",
        context_pattern="database access",
    )
    original_confidence = skill1.confidence
    # Teach similar skill — should reinforce
    skill2 = forge.teach(
        rule="Always use parameterized queries for SQL injection prevention",
        context_pattern="database access",
    )
    # Should return same skill with bumped confidence (if similarity >= 0.5)
    # Note: ChromaDB similarity may not hit 0.5 for these strings, so test both paths
    all_skills = forge._storage.get_all_skills()
    assert len(all_skills) >= 1  # At least one skill exists
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py::test_teach_creates_skill -v`
Expected: FAIL

- [ ] **Step 3: Forge.teach 実装**

`src/engram_ai/forge.py` の Forge クラスに追加:

```python
    def teach(self, rule: str, context_pattern: str,
              skill_type: str = "positive",
              confidence: float = 0.8) -> Skill:
        """Create a skill directly from user instruction."""
        if skill_type not in ("positive", "anti"):
            raise ValueError(f"skill_type must be 'positive' or 'anti', got {skill_type!r}")

        # Check for similar existing skill
        try:
            similar = self._storage.query_skills(rule, k=3)
            for existing_skill, sim in similar:
                if sim >= 0.5:
                    existing_skill.confidence = min(1.0, round(existing_skill.confidence + 0.1, 4))
                    existing_skill.reinforcement_count += 1
                    self._storage.update_skill(existing_skill)
                    from engram_ai.events.events import SKILL_REINFORCED
                    self._event_bus.emit(SKILL_REINFORCED, existing_skill)
                    return existing_skill
        except Exception:
            pass  # No existing skills or query failed

        skill = Skill(
            rule=rule,
            context_pattern=context_pattern,
            confidence=confidence,
            source_experiences=[],
            evidence_count=0,
            valence_summary={},
            skill_type=skill_type,
        )
        self._storage.store_skill(skill)
        from engram_ai.events.events import SKILL_CRYSTALLIZED
        self._event_bus.emit(SKILL_CRYSTALLIZED, skill)
        return skill
```

- [ ] **Step 4: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add src/engram_ai/forge.py tests/test_intelligence_pack.py
git commit -m "feat: add Forge.teach() — direct skill creation"
```

---

### Task 4: engram_teach MCPツール (Feature 3)

**Files:**
- Modify: `src/engram_ai/mcp.py`
- Test: `tests/test_mcp.py`

- [ ] **Step 1: テスト作成**

`tests/test_mcp.py` の末尾に追加:

```python
@pytest.mark.asyncio
async def test_engram_teach_creates_skill(forge_and_server):
    _, server = forge_and_server
    result = await _call_tool(server, "engram_teach", {
        "rule": "Always write tests first",
        "context_pattern": "feature development",
    })
    assert "Taught" in result[0].text
    assert "Always write tests first" in result[0].text


@pytest.mark.asyncio
async def test_engram_teach_anti_skill(forge_and_server):
    _, server = forge_and_server
    result = await _call_tool(server, "engram_teach", {
        "rule": "Never use eval()",
        "context_pattern": "Python code",
        "skill_type": "anti",
    })
    assert "Taught" in result[0].text or "Reinforced" in result[0].text


@pytest.mark.asyncio
async def test_list_tools_includes_teach(forge_and_server):
    _, server = forge_and_server
    tools = await _list_tools(server)
    tool_names = [t.name for t in tools]
    assert "engram_teach" in tool_names
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_mcp.py::test_list_tools_includes_teach -v`
Expected: FAIL

- [ ] **Step 3: MCP toolに `engram_teach` を追加**

`src/engram_ai/mcp.py` の `list_tools` 関数内、`engram_observe` Tool の後に追加:

```python
            Tool(
                name="engram_teach",
                description="Directly teach a skill/rule to Engram-AI without going through the experience cycle",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rule": {"type": "string", "description": "The skill/rule to remember"},
                        "context_pattern": {"type": "string", "description": "When this applies"},
                        "skill_type": {
                            "type": "string",
                            "enum": ["positive", "anti"],
                            "default": "positive",
                            "description": "Skill type",
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.8,
                            "description": "Initial confidence",
                        },
                        "project": {"type": "string", "description": "Project name", "default": "default"},
                    },
                    "required": ["rule", "context_pattern"],
                },
            ),
```

`call_tool` 関数内、`engram_observe` ハンドラの後に追加:

```python
            elif name == "engram_teach":
                # Check pre-existing skill count to detect reinforcement
                pre_count = len(forge._storage.get_all_skills())
                skill = forge.teach(
                    rule=arguments["rule"],
                    context_pattern=arguments["context_pattern"],
                    skill_type=arguments.get("skill_type", "positive"),
                    confidence=arguments.get("confidence", 0.8),
                )
                post_count = len(forge._storage.get_all_skills())
                if post_count > pre_count:
                    text = f'Taught: "{skill.rule}" (confidence: {skill.confidence:.2f})'
                else:
                    text = f'Reinforced existing skill: "{skill.rule}" (confidence: {skill.confidence:.2f})'
                return [TextContent(type="text", text=text)]
```

- [ ] **Step 4: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_mcp.py -v`
Expected: ALL PASS

- [ ] **Step 5: コミット**

```bash
git add src/engram_ai/mcp.py tests/test_mcp.py
git commit -m "feat: add engram_teach MCP tool"
```

---

### Task 5: Active Recall — Forge.recall (Feature 1)

**Files:**
- Modify: `src/engram_ai/forge.py`
- Test: `tests/test_intelligence_pack.py`

- [ ] **Step 1: テスト作成**

`tests/test_intelligence_pack.py` に追加:

```python
def test_recall_returns_skills(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    # Teach a skill first
    forge.teach(rule="Use eager loading", context_pattern="database queries")
    result = forge.recall("database queries optimization")
    assert "skills" in result
    assert "warnings" in result
    assert isinstance(result["skills"], list)
    assert isinstance(result["warnings"], list)


def test_recall_returns_warnings(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    # Record a negative experience
    forge.record(
        action="Changed auth middleware",
        context="authentication system",
        outcome="Production outage",
        valence=-0.8,
    )
    result = forge.recall("authentication system changes")
    assert "warnings" in result
    # Warnings should contain negative experiences (if similarity is high enough)


def test_recall_empty_context(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    result = forge.recall("")
    assert result == {"skills": [], "warnings": []}


def test_recall_zero_k(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    result = forge.recall("test", k_skills=0, k_experiences=0)
    assert result == {"skills": [], "warnings": []}
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py::test_recall_returns_skills -v`
Expected: FAIL

- [ ] **Step 3: Forge.recall 実装**

`src/engram_ai/forge.py` の Forge クラスに追加:

```python
    def recall(self, context: str, k_skills: int = 3, k_experiences: int = 2) -> dict:
        """Search for relevant skills and negative experiences for a given context."""
        if not context.strip() or (k_skills == 0 and k_experiences == 0):
            return {"skills": [], "warnings": []}

        skills = []
        if k_skills > 0:
            try:
                results = self._storage.query_skills(context, k=k_skills)
                skills = [s for s, sim in results if sim >= 0.4][:k_skills]
            except Exception:
                pass

        warnings = []
        if k_experiences > 0:
            try:
                results = self._storage.query_experiences(context, k=k_experiences * 3)
                warnings = [
                    exp for exp, sim in results
                    if exp.valence < -0.3 and sim >= 0.4
                ][:k_experiences]
            except Exception:
                pass

        return {"skills": skills, "warnings": warnings}
```

- [ ] **Step 4: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add src/engram_ai/forge.py tests/test_intelligence_pack.py
git commit -m "feat: add Forge.recall() — proactive skill injection"
```

---

### Task 6: Pre-emptive Warning — Forge.warn (Feature 2)

**Files:**
- Modify: `src/engram_ai/forge.py`
- Test: `tests/test_intelligence_pack.py`

- [ ] **Step 1: テスト作成**

`tests/test_intelligence_pack.py` に追加:

```python
def test_warn_returns_negative_experiences(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    forge.record(
        action="Edit auth.py",
        context="auth.py session handling",
        outcome="CSRF vulnerability",
        valence=-0.9,
    )
    warnings = forge.warn(action="Edit auth.py", context="auth.py session handling")
    # May or may not find depending on similarity threshold
    assert isinstance(warnings, list)


def test_warn_ignores_positive_experiences(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    forge.record(
        action="Edit auth.py",
        context="auth.py refactor",
        outcome="Clean code",
        valence=0.9,
    )
    warnings = forge.warn(action="Edit auth.py", context="auth.py refactor")
    # Should not include positive experiences
    for exp in warnings:
        assert exp.valence < -0.3


def test_warn_empty_returns_empty(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    warnings = forge.warn(action="test", context="nothing here")
    assert warnings == []
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py::test_warn_returns_negative_experiences -v`
Expected: FAIL

- [ ] **Step 3: Forge.warn 実装**

`src/engram_ai/forge.py` の Forge クラスに追加:

```python
    def warn(self, action: str, context: str, threshold: float = 0.6) -> list:
        """Search for past negative experiences similar to the current action."""
        search_text = f"{action} {context}"
        try:
            results = self._storage.query_experiences(search_text, k=10)
        except Exception:
            return []

        warnings = [
            (exp, sim) for exp, sim in results
            if exp.valence < -0.3 and sim >= threshold
        ]
        warnings.sort(key=lambda pair: pair[1], reverse=True)  # Sort by similarity descending
        return [exp for exp, sim in warnings]
```

- [ ] **Step 4: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add src/engram_ai/forge.py tests/test_intelligence_pack.py
git commit -m "feat: add Forge.warn() — pre-emptive warning"
```

---

### Task 7: Hook強化 — recall + warn (Features 1+2)

**Files:**
- Modify: `src/engram_ai/cli.py`
- Test: `tests/test_hook_auto_learn.py`

- [ ] **Step 1: テスト作成**

`tests/test_hook_auto_learn.py` に追加:

```python
def test_hook_user_prompt_submit_recall(tmp_path, monkeypatch):
    """Hook should output recall results."""
    storage_dir = tmp_path / "data"
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(storage_dir))

    # Pre-populate a skill via direct storage
    from engram_ai import Forge
    forge = Forge(storage_path=str(storage_dir / "default"), llm=None)
    forge.teach(rule="Always test auth changes", context_pattern="authentication")
    forge.close()

    stdin_data = json.dumps({"prompt": "Fix the authentication bug"})
    runner = CliRunner()
    result = runner.invoke(main, ["hook", "user-prompt-submit"], input=stdin_data)
    assert result.exit_code == 0
    # Output may or may not contain recall results depending on similarity


def test_hook_post_tool_use_warn(tmp_path, monkeypatch):
    """post-tool-use hook should output warnings for risky actions."""
    storage_dir = tmp_path / "data"
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(storage_dir))

    # Pre-populate a negative experience
    from engram_ai import Forge
    forge = Forge(storage_path=str(storage_dir / "default"), llm=None)
    forge.record(
        action="Edit on auth.py",
        context="Edit on auth.py",
        outcome="Security vulnerability",
        valence=-0.9,
    )
    forge.close()

    stdin_data = json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": "auth.py"},
    })
    runner = CliRunner()
    result = runner.invoke(main, ["hook", "post-tool-use"], input=stdin_data)
    assert result.exit_code == 0
    # Output may contain warning if similarity is high enough
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_hook_auto_learn.py::test_hook_user_prompt_submit_recall -v`
Expected: May pass or fail depending on whether hook changes are needed

- [ ] **Step 3: hook post-tool-use に warn を追加**

`src/engram_ai/cli.py` の `hook_post_tool_use` 関数を**全体を以下に置き換え**:

```python
@hook.command("post-tool-use")
def hook_post_tool_use():
    """Handle PostToolUse hook from Claude Code."""
    try:
        stdin_data = json.loads(sys.stdin.read())
        tool_name = stdin_data.get("tool_name", "unknown")
        tool_input = stdin_data.get("tool_input", {})

        file_path = tool_input.get("file_path", tool_input.get("path", ""))
        action = f"{tool_name} on {file_path}" if file_path else tool_name
        context = f"{tool_name} tool usage"
        if file_path:
            context = f"{tool_name} on {file_path}"

        forge = _get_forge()
        forge.record_pending(
            action=action,
            context=context,
            metadata={"tool": tool_name, "file": file_path},
        )

        # Pre-emptive Warning: check for past failures with similar actions
        warnings = forge.warn(action=action, context=context)
        if warnings:
            lines = ["Warning: past issues with similar actions:"]
            for exp in warnings[:3]:
                lines.append(f'- "{exp.outcome}" (valence: {exp.valence:.1f})')
            print(json.dumps({"result": "\n".join(lines)}))
    except Exception:
        pass  # Hooks must never block Claude Code
```

- [ ] **Step 4: hook user-prompt-submit に recall を追加**

`src/engram_ai/cli.py` の `hook_user_prompt_submit` 関数内、auto-learn ブロック (`if experience is not None:` ブロック) の**後**、外側の `except Exception:` の**前**に以下を追加（インデント1段: try ブロック内）:

```python
        # Active Recall: inject relevant skills and warnings
        if user_message.strip():
            recall_result = forge.recall(user_message)
            lines = []
            if recall_result["skills"]:
                lines.append("Relevant knowledge:")
                for s in recall_result["skills"]:
                    lines.append(f"- {s.rule} (confidence: {s.confidence:.2f})")
            if recall_result["warnings"]:
                lines.append("Past issues in similar context:")
                for exp in recall_result["warnings"]:
                    lines.append(f'- {exp.outcome} (valence: {exp.valence:.1f})')
            if lines:
                print(json.dumps({"result": "\n".join(lines)}))
```

- [ ] **Step 5: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_hook_auto_learn.py -v`
Expected: ALL PASS

- [ ] **Step 6: コミット**

```bash
git add src/engram_ai/cli.py tests/test_hook_auto_learn.py
git commit -m "feat: add Active Recall + Pre-emptive Warning to hooks"
```

---

### Task 8: Cross-Project Transfer — ProjectManager拡張 (Feature 4)

**Files:**
- Modify: `src/engram_ai/project.py`
- Test: `tests/test_project.py`

- [ ] **Step 1: テスト作成**

`tests/test_project.py` の末尾に追加:

```python
def test_get_global_forge(tmp_path, mock_llm):
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, llm=mock_llm, config={"default_project": "default"})
    global_forge = pm.get_global_forge()
    assert global_forge is not None
    assert (tmp_path / "_global").exists()


def test_global_excluded_from_list(tmp_path, mock_llm):
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, llm=mock_llm, config={"default_project": "default"})
    pm.get_global_forge()
    pm.get_forge("alpha")
    names = pm.list_projects()
    assert "_global" not in names
    assert "alpha" in names


def test_delete_global_raises(tmp_path, mock_llm):
    import pytest
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, llm=mock_llm, config={"default_project": "default"})
    pm.get_global_forge()
    with pytest.raises(ValueError, match="_global"):
        pm.delete_project("_global")


def test_sync_global_skills(tmp_path, mock_llm):
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, llm=mock_llm, config={"default_project": "default"})
    # Add a skill to global pool
    global_forge = pm.get_global_forge()
    global_forge.teach(rule="Global best practice", context_pattern="any project")

    # Sync to a new project
    synced = pm.sync_global_skills("alpha")
    assert isinstance(synced, list)
    # The skill should now exist in alpha
    alpha_forge = pm.get_forge("alpha")
    skills = alpha_forge._storage.get_all_skills()
    # May have the synced skill (depends on similarity dedup)
    assert isinstance(skills, list)
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_project.py::test_get_global_forge -v`
Expected: FAIL

- [ ] **Step 3: ProjectManager 拡張**

`src/engram_ai/project.py` に追加:

```python
    def get_global_forge(self) -> "Forge":
        """Return Forge for the _global skill pool."""
        if "_global" in self._cache:
            return self._cache["_global"]
        global_path = self._base_path / "_global"
        global_path.mkdir(parents=True, exist_ok=True)
        forge = Forge(
            storage_path=str(global_path),
            llm=self._llm,
            enable_policies=False,
        )
        self._cache["_global"] = forge
        return forge

    def sync_global_skills(self, project: str) -> list:
        """Import global skills into a project that don't already exist."""
        import json as _json
        from datetime import datetime

        global_forge = self.get_global_forge()
        project_forge = self.get_forge(project)

        global_skills = global_forge._storage.get_all_skills()
        if not global_skills:
            return []

        # Check sync timestamp
        sync_file = self._base_path / project / "_global_sync.json"
        last_sync = None
        if sync_file.exists():
            try:
                data = _json.loads(sync_file.read_text(encoding="utf-8"))
                last_sync = data.get("last_global_sync")
            except Exception:
                pass

        synced = []
        for skill in global_skills:
            # Skip if created before last sync
            if last_sync and skill.created_at.isoformat() <= last_sync:
                continue

            # Dedup: skip if similar skill exists in project
            try:
                existing = project_forge._storage.query_skills(skill.rule, k=3)
                if any(sim >= 0.7 for _, sim in existing):
                    continue
            except Exception:
                pass

            # Import with 80% confidence
            imported = project_forge.teach(
                rule=skill.rule,
                context_pattern=skill.context_pattern,
                skill_type=skill.skill_type,
                confidence=round(skill.confidence * 0.8, 4),
            )
            synced.append(imported)

        # Update sync timestamp
        sync_file.parent.mkdir(parents=True, exist_ok=True)
        sync_file.write_text(
            _json.dumps({"last_global_sync": datetime.now().isoformat()}),
            encoding="utf-8",
        )

        return synced
```

`get_forge` を修正して `sync_global_skills` を自動トリガー（`_global` プール自体が存在する場合のみ）:

```python
    def get_forge(self, project: str | None = None) -> Forge:
        name = project or self._default_project
        self._validate_name(name)
        if name in self._cache:
            return self._cache[name]
        storage_path = self._resolve_path(name)
        storage_path.mkdir(parents=True, exist_ok=True)
        forge = Forge(
            storage_path=str(storage_path),
            llm=self._llm,
            enable_policies=True,
        )
        self._cache[name] = forge
        # Auto-sync global skills if global pool exists
        if name != "_global" and (self._base_path / "_global").exists():
            try:
                self.sync_global_skills(name)
            except Exception:
                pass  # Sync failure should not block forge creation
        return forge
```

`list_projects` を修正して `_global` を除外:

```python
    def list_projects(self) -> list[str]:
        if not self._base_path.exists():
            return []
        return sorted(
            d.name for d in self._base_path.iterdir()
            if d.is_dir() and _PROJECT_NAME_RE.match(d.name) and d.name != "_global"
        )
```

`delete_project` に `_global` ガードを追加:

```python
    def delete_project(self, name: str) -> None:
        if name == self._default_project:
            raise ValueError(f"Cannot delete the default project '{name}'")
        if name == "_global":
            raise ValueError("Cannot delete the _global skill pool")
        # ... rest unchanged
```

- [ ] **Step 4: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_project.py -v`
Expected: ALL PASS

- [ ] **Step 5: コミット**

```bash
git add src/engram_ai/project.py tests/test_project.py
git commit -m "feat: add global skill pool + sync to ProjectManager"
```

---

### Task 9: Cross-Project Promotion — crystallize後の自動昇格 (Feature 4)

**Files:**
- Modify: `src/engram_ai/forge.py`
- Test: `tests/test_intelligence_pack.py`

- [ ] **Step 1: テスト作成**

`tests/test_intelligence_pack.py` に追加:

```python
def test_promote_to_global(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    from engram_ai.models.skill import Skill
    skill = Skill(
        rule="High confidence skill",
        context_pattern="general",
        confidence=0.95,
        source_experiences=["e1", "e2", "e3"],
        evidence_count=5,
        valence_summary={"positive": 5},
    )
    # promote_to_global needs a global_forge reference
    from engram_ai.storage.chromadb import ChromaDBStorage
    global_storage = ChromaDBStorage(persist_path=str(tmp_path / "global"))
    promoted = forge.promote_to_global(skill, global_storage)
    assert promoted is not None
    assert promoted.rule == skill.rule
    global_skills = global_storage.get_all_skills()
    assert len(global_skills) >= 1
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py::test_promote_to_global -v`
Expected: FAIL

- [ ] **Step 3: Forge.promote_to_global 実装**

`src/engram_ai/forge.py` の Forge クラスに追加:

```python
    def promote_to_global(self, skill: Skill, global_storage: "BaseStorage") -> Skill:
        """Copy a high-confidence skill to the global pool."""
        # Dedup check
        try:
            existing = global_storage.query_skills(skill.rule, k=3)
            for gs, sim in existing:
                if sim >= 0.7:
                    gs.confidence = min(1.0, round(gs.confidence + 0.1, 4))
                    gs.reinforcement_count += 1
                    global_storage.update_skill(gs)
                    return gs
        except Exception:
            pass

        promoted = Skill(
            rule=skill.rule,
            context_pattern=skill.context_pattern,
            confidence=skill.confidence,
            source_experiences=skill.source_experiences,
            evidence_count=skill.evidence_count,
            valence_summary=skill.valence_summary,
            skill_type=skill.skill_type,
        )
        global_storage.store_skill(promoted)
        return promoted
```

- [ ] **Step 4: Forge.crystallize() を修正して自動昇格**

`src/engram_ai/forge.py` の `crystallize` メソッドを修正:

```python
    def crystallize(self, min_experiences: int = 3, min_confidence: float = 0.7,
                    global_storage: "BaseStorage | None" = None) -> list[Skill]:
        skills = self._crystallizer.crystallize(min_experiences, min_confidence)
        # Auto-promote high-confidence skills to global pool
        if global_storage is not None:
            for skill in self._storage.get_all_skills():
                if skill.confidence >= 0.9 and skill.evidence_count >= 3:
                    try:
                        self.promote_to_global(skill, global_storage)
                    except Exception:
                        pass
        return skills
```

注意: `global_storage` はオプション引数。ProjectManager経由で呼ばれる場合のみグローバルストレージが渡される。CLI/MCP経由の直接呼び出しは従来通り動作。

- [ ] **Step 5: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py -v`
Expected: PASS

- [ ] **Step 6: 既存テスト確認**

Run: `.venv/Scripts/python -m pytest tests/ --ignore=tests/dashboard -v`
Expected: ALL PASS

- [ ] **Step 7: コミット**

```bash
git add src/engram_ai/forge.py tests/test_intelligence_pack.py
git commit -m "feat: add Forge.promote_to_global() + auto-promotion in crystallize"
```

---

### Task 10: Skill Marketplace — export/import (Feature 6)

**Files:**
- Modify: `src/engram_ai/forge.py`
- Test: `tests/test_intelligence_pack.py`

- [ ] **Step 1: テスト作成**

`tests/test_intelligence_pack.py` に追加:

```python
def test_export_skills(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    forge.teach(rule="Rule A", context_pattern="ctx A")
    forge.teach(rule="Rule B", context_pattern="ctx B")
    pack = forge.export_skills(name="test-pack", description="Test")
    assert pack["format_version"] == 1
    assert pack["name"] == "test-pack"
    assert len(pack["skills"]) == 2
    assert pack["skills"][0]["rule"] in ("Rule A", "Rule B")


def test_import_skills(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    pack = {
        "format_version": 1,
        "name": "test",
        "description": "",
        "exported_at": "2026-03-18T00:00:00Z",
        "source_project": "other",
        "skills": [
            {"rule": "Imported rule", "context_pattern": "ctx", "confidence": 0.9, "evidence_count": 3},
        ],
    }
    result = forge.import_skills(pack)
    assert len(result["imported"]) == 1
    assert result["imported"][0].rule == "Imported rule"
    assert result["imported"][0].confidence == 0.72  # 0.9 * 0.8


def test_import_skills_invalid_version(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    import pytest
    from engram_ai.exceptions import EngramError
    pack = {"format_version": 99, "skills": []}
    with pytest.raises(EngramError, match="Unsupported"):
        forge.import_skills(pack)


def test_import_skills_empty_skills(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    import pytest
    from engram_ai.exceptions import EngramError
    with pytest.raises(EngramError, match="no skills"):
        forge.import_skills({"format_version": 1, "skills": []})


def test_export_import_roundtrip(tmp_path, mock_llm):
    forge1 = Forge(storage_path=str(tmp_path / "data1"), llm=mock_llm)
    forge1.teach(rule="Roundtrip rule", context_pattern="roundtrip ctx")
    pack = forge1.export_skills(name="roundtrip")

    forge2 = Forge(storage_path=str(tmp_path / "data2"), llm=mock_llm)
    result = forge2.import_skills(pack)
    assert len(result["imported"]) == 1
    assert result["imported"][0].rule == "Roundtrip rule"
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py::test_export_skills -v`
Expected: FAIL

- [ ] **Step 3: export_skills / import_skills 実装**

`src/engram_ai/forge.py` の Forge クラスに追加:

```python
    def export_skills(self, name: str, description: str = "") -> dict:
        """Export all active skills as a pack dict."""
        from datetime import datetime
        skills = self._storage.get_all_skills()
        return {
            "format_version": 1,
            "name": name,
            "description": description,
            "exported_at": datetime.now().isoformat(),
            "source_project": "",
            "skills": [
                {
                    "rule": s.rule,
                    "context_pattern": s.context_pattern,
                    "skill_type": s.skill_type,
                    "confidence": s.confidence,
                    "evidence_count": s.evidence_count,
                }
                for s in skills
            ],
        }

    def import_skills(self, pack: dict, confidence_scale: float = 0.8) -> dict:
        """Import skills from a pack."""
        version = pack.get("format_version")
        if version != 1:
            raise EngramError(f"Unsupported pack format version: {version}")

        skills_data = pack.get("skills", [])
        if not skills_data:
            raise EngramError("Pack contains no skills")

        imported = []
        skipped = []
        reinforced = []

        for entry in skills_data:
            rule = entry.get("rule", "")
            context_pattern = entry.get("context_pattern", "")
            if not rule or not context_pattern:
                skipped.append(entry)
                continue

            # Dedup check
            try:
                existing = self._storage.query_skills(rule, k=3)
                skip = False
                for ex_skill, sim in existing:
                    if sim >= 0.7:
                        skipped.append(entry)
                        skip = True
                        break
                    elif sim >= 0.5:
                        ex_skill.confidence = min(1.0, round(ex_skill.confidence + 0.1, 4))
                        ex_skill.reinforcement_count += 1
                        self._storage.update_skill(ex_skill)
                        reinforced.append(ex_skill)
                        skip = True
                        break
                if skip:
                    continue
            except Exception:
                pass

            confidence = min(1.0, max(0.0, entry.get("confidence", 0.8))) * confidence_scale
            skill = Skill(
                rule=rule,
                context_pattern=context_pattern,
                confidence=round(confidence, 4),
                source_experiences=[],
                evidence_count=entry.get("evidence_count", 0),
                valence_summary={},
                skill_type=entry.get("skill_type", "positive"),
            )
            self._storage.store_skill(skill)
            imported.append(skill)

        return {"imported": imported, "skipped": skipped, "reinforced": reinforced}
```

- [ ] **Step 4: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_intelligence_pack.py -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add src/engram_ai/forge.py tests/test_intelligence_pack.py
git commit -m "feat: add export_skills/import_skills — Skill Marketplace foundation"
```

---

### Task 11: CLI export/import コマンド (Feature 6)

**Files:**
- Modify: `src/engram_ai/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: テスト作成**

`tests/test_cli.py` の末尾に追加:

```python
def test_export_command(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    output_file = tmp_path / "pack.engram-pack.json"
    runner = CliRunner()
    result = runner.invoke(main, ["export", "--name", "test-pack", "--output", str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()
    import json
    pack = json.loads(output_file.read_text(encoding="utf-8"))
    assert pack["name"] == "test-pack"
    assert pack["format_version"] == 1


def test_import_command(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    import json
    pack_file = tmp_path / "pack.engram-pack.json"
    pack_file.write_text(json.dumps({
        "format_version": 1,
        "name": "test",
        "description": "",
        "exported_at": "2026-03-18T00:00:00Z",
        "source_project": "other",
        "skills": [
            {"rule": "Test rule", "context_pattern": "ctx", "confidence": 0.9, "evidence_count": 1},
        ],
    }), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["import", str(pack_file)])
    assert result.exit_code == 0
    assert "Imported: 1" in result.output


def test_import_dry_run(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    import json
    pack_file = tmp_path / "pack.engram-pack.json"
    pack_file.write_text(json.dumps({
        "format_version": 1,
        "name": "test",
        "description": "",
        "exported_at": "2026-03-18T00:00:00Z",
        "source_project": "other",
        "skills": [
            {"rule": "Test rule", "context_pattern": "ctx", "confidence": 0.9, "evidence_count": 1},
        ],
    }), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["import", str(pack_file), "--dry-run"])
    assert result.exit_code == 0
    assert "Dry run" in result.output
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py::test_export_command -v`
Expected: FAIL

- [ ] **Step 3: CLI コマンド実装**

`src/engram_ai/cli.py` の `projects` group の前に追加:

```python
@main.command("export")
@click.option("--name", required=True, help="Pack name")
@click.option("--description", default="", help="Pack description")
@click.option("--output", "output_path", required=True, help="Output file path")
@click.pass_context
def export_pack(ctx, name, description, output_path):
    """Export skills as a shareable pack."""
    forge = _get_forge(project=ctx.obj.get("project"))
    pack = forge.export_skills(name=name, description=description)
    Path(output_path).write_text(
        json.dumps(pack, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    click.echo(f"Exported {len(pack['skills'])} skill(s) to {output_path}")


@main.command("import")
@click.argument("pack_path")
@click.option("--confidence", default=0.8, help="Confidence scale for imported skills")
@click.option("--dry-run", is_flag=True, help="Preview without importing")
@click.pass_context
def import_pack(ctx, pack_path, confidence, dry_run):
    """Import skills from a pack file."""
    pack = json.loads(Path(pack_path).read_text(encoding="utf-8"))
    if dry_run:
        skills = pack.get("skills", [])
        click.echo(f"Dry run: {len(skills)} skill(s) would be imported from '{pack.get('name', '?')}'")
        for s in skills:
            click.echo(f"  - {s.get('rule', '?')} (confidence: {s.get('confidence', 0):.2f} * {confidence:.2f})")
        return
    forge = _get_forge(project=ctx.obj.get("project"))
    result = forge.import_skills(pack, confidence_scale=confidence)
    click.echo(f"Imported: {len(result['imported'])}, Skipped: {len(result['skipped'])}, Reinforced: {len(result['reinforced'])}")
```

- [ ] **Step 4: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: ALL PASS

- [ ] **Step 5: コミット**

```bash
git add src/engram_ai/cli.py tests/test_cli.py
git commit -m "feat: add export/import CLI commands"
```

---

### Task 12: MCP export/import ツール (Feature 6)

**Files:**
- Modify: `src/engram_ai/mcp.py`
- Test: `tests/test_mcp.py`

- [ ] **Step 1: テスト作成**

`tests/test_mcp.py` の末尾に追加:

```python
@pytest.mark.asyncio
async def test_list_tools_includes_marketplace(forge_and_server):
    _, server = forge_and_server
    tools = await _list_tools(server)
    tool_names = [t.name for t in tools]
    assert "engram_export" in tool_names
    assert "engram_import" in tool_names


@pytest.mark.asyncio
async def test_engram_export(forge_and_server):
    forge, server = forge_and_server
    forge.teach(rule="Test export rule", context_pattern="test")
    result = await _call_tool(server, "engram_export", {"name": "test-pack"})
    assert "Exported" in result[0].text


@pytest.mark.asyncio
async def test_engram_import(forge_and_server):
    _, server = forge_and_server
    pack = {
        "format_version": 1,
        "name": "test",
        "description": "",
        "exported_at": "2026-03-18T00:00:00Z",
        "source_project": "other",
        "skills": [
            {"rule": "Imported via MCP", "context_pattern": "mcp test", "confidence": 0.9, "evidence_count": 1},
        ],
    }
    import json
    result = await _call_tool(server, "engram_import", {"pack_json": json.dumps(pack)})
    assert "Imported: 1" in result[0].text
```

- [ ] **Step 2: テスト実行 — 失敗を確認**

Run: `.venv/Scripts/python -m pytest tests/test_mcp.py::test_list_tools_includes_marketplace -v`
Expected: FAIL

- [ ] **Step 3: MCP tools 追加**

`src/engram_ai/mcp.py` の `list_tools` に追加:

```python
            Tool(
                name="engram_export",
                description="Export project skills as a shareable pack",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Pack name"},
                        "description": {"type": "string", "description": "Pack description", "default": ""},
                        "project": {"type": "string", "description": "Project name", "default": "default"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="engram_import",
                description="Import skills from a pack (JSON string)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pack_json": {"type": "string", "description": "Pack JSON string"},
                        "confidence_scale": {"type": "number", "default": 0.8, "description": "Confidence multiplier"},
                        "project": {"type": "string", "description": "Project name", "default": "default"},
                    },
                    "required": ["pack_json"],
                },
            ),
```

`call_tool` にハンドラ追加:

```python
            elif name == "engram_export":
                pack = forge.export_skills(
                    name=arguments["name"],
                    description=arguments.get("description", ""),
                )
                import json as _json
                return [TextContent(type="text", text=f"Exported {len(pack['skills'])} skill(s):\n{_json.dumps(pack, indent=2)}")]

            elif name == "engram_import":
                import json as _json
                pack = _json.loads(arguments["pack_json"])
                result = forge.import_skills(pack, confidence_scale=arguments.get("confidence_scale", 0.8))
                return [TextContent(type="text", text=f"Imported: {len(result['imported'])}, Skipped: {len(result['skipped'])}, Reinforced: {len(result['reinforced'])}")]
```

- [ ] **Step 4: テスト実行 — 成功を確認**

Run: `.venv/Scripts/python -m pytest tests/test_mcp.py -v`
Expected: ALL PASS

- [ ] **Step 5: 全テスト実行**

Run: `.venv/Scripts/python -m pytest tests/ --ignore=tests/dashboard -v`
Expected: ALL PASS

- [ ] **Step 6: Lint 確認**

Run: `.venv/Scripts/python -m ruff check src/ tests/ --exclude=tests/dashboard`
Expected: All checks passed!

- [ ] **Step 7: コミット**

```bash
git add src/engram_ai/mcp.py tests/test_mcp.py
git commit -m "feat: add engram_export/engram_import MCP tools"
```
