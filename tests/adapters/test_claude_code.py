import pytest
from engram_ai.adapters.claude_code import ClaudeCodeAdapter

@pytest.fixture
def claude_md(tmp_path):
    path = tmp_path / "CLAUDE.md"
    path.write_text("# Project Rules\n- Use TypeScript\n", encoding="utf-8")
    return path

@pytest.fixture
def adapter():
    from engram_ai.adapters.claude_code import ClaudeCodeAdapter
    return ClaudeCodeAdapter()

def test_write_skills_creates_section(adapter, claude_md):
    skills_text = "- Avoid Optional (confidence: 0.85)\n"
    adapter.write_skills(str(claude_md), skills_text)
    content = claude_md.read_text(encoding="utf-8")
    assert "# Project Rules" in content
    assert "- Use TypeScript" in content
    assert "<!-- engram-ai:start -->" in content
    assert "Avoid Optional" in content
    assert "<!-- engram-ai:end -->" in content

def test_write_skills_updates_existing_section(adapter, claude_md):
    adapter.write_skills(str(claude_md), "- Skill A\n")
    adapter.write_skills(str(claude_md), "- Skill B\n")
    content = claude_md.read_text(encoding="utf-8")
    assert content.count("<!-- engram-ai:start -->") == 1
    assert "Skill A" not in content
    assert "Skill B" in content

def test_write_skills_preserves_existing_content(adapter, claude_md):
    claude_md.write_text("# Rules\n- Rule 1\n\nSome text\n\n# Other\n- Other stuff\n", encoding="utf-8")
    adapter.write_skills(str(claude_md), "- New skill\n")
    content = claude_md.read_text(encoding="utf-8")
    assert "- Rule 1" in content
    assert "Some text" in content
    assert "# Other" in content
    assert "- Other stuff" in content
    assert "- New skill" in content

def test_write_skills_creates_file_if_missing(adapter, tmp_path):
    path = tmp_path / "NEW_CLAUDE.md"
    adapter.write_skills(str(path), "- First skill\n")
    content = path.read_text(encoding="utf-8")
    assert "<!-- engram-ai:start -->" in content
    assert "First skill" in content

def test_read_current_config(adapter, claude_md):
    content = adapter.read_config(str(claude_md))
    assert "Project Rules" in content


def test_write_anti_skills_new_file(tmp_path):
    adapter = ClaudeCodeAdapter()
    path = str(tmp_path / "CLAUDE.md")
    adapter.write_anti_skills(path, "- Never store tokens in query params")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "<!-- engram-ai:anti-skills:start -->" in content
    assert "Anti-Patterns (Avoid)" in content
    assert "Never store tokens" in content
    assert "<!-- engram-ai:anti-skills:end -->" in content


def test_write_anti_skills_replaces_existing(tmp_path):
    adapter = ClaudeCodeAdapter()
    path = str(tmp_path / "CLAUDE.md")
    (tmp_path / "CLAUDE.md").write_text(
        "before\n<!-- engram-ai:anti-skills:start -->\nold\n<!-- engram-ai:anti-skills:end -->\nafter\n"
    )
    adapter.write_anti_skills(path, "- New anti-pattern")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "New anti-pattern" in content
    assert "old" not in content
    assert "before" in content
    assert "after" in content


def test_write_skills_and_anti_skills_coexist(tmp_path):
    adapter = ClaudeCodeAdapter()
    path = str(tmp_path / "CLAUDE.md")
    adapter.write_skills(path, "- Use schema validation")
    adapter.write_anti_skills(path, "- Never use eval()")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "<!-- engram-ai:start -->" in content
    assert "Use schema validation" in content
    assert "<!-- engram-ai:anti-skills:start -->" in content
    assert "Never use eval()" in content
