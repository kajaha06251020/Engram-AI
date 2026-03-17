from engram_ai.adapters.windsurf import WindsurfAdapter


def test_write_skills(tmp_path):
    adapter = WindsurfAdapter()
    path = str(tmp_path / ".windsurfrules")
    adapter.write_skills(path, "- Use schema validation")
    content = (tmp_path / ".windsurfrules").read_text()
    assert "# --- engram-ai:start ---" in content
    assert "Use schema validation" in content


def test_write_anti_skills(tmp_path):
    adapter = WindsurfAdapter()
    path = str(tmp_path / ".windsurfrules")
    adapter.write_anti_skills(path, "- Never use eval()")
    content = (tmp_path / ".windsurfrules").read_text()
    assert "# --- engram-ai:anti-skills:start ---" in content


def test_read_config(tmp_path):
    adapter = WindsurfAdapter()
    (tmp_path / ".windsurfrules").write_text("rules")
    assert "rules" in adapter.read_config(str(tmp_path / ".windsurfrules"))
