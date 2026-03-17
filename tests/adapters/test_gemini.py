from engram_ai.adapters.gemini import GeminiAdapter


def test_write_skills(tmp_path):
    adapter = GeminiAdapter()
    path = str(tmp_path / "GEMINI.md")
    adapter.write_skills(path, "- Use schema validation")
    content = (tmp_path / "GEMINI.md").read_text()
    assert "<!-- engram-ai:start -->" in content
    assert "Use schema validation" in content


def test_write_anti_skills(tmp_path):
    adapter = GeminiAdapter()
    path = str(tmp_path / "GEMINI.md")
    adapter.write_anti_skills(path, "- Never use eval()")
    content = (tmp_path / "GEMINI.md").read_text()
    assert "<!-- engram-ai:anti-skills:start -->" in content
    assert "Never use eval()" in content


def test_read_config(tmp_path):
    adapter = GeminiAdapter()
    (tmp_path / "GEMINI.md").write_text("rules")
    assert "rules" in adapter.read_config(str(tmp_path / "GEMINI.md"))
