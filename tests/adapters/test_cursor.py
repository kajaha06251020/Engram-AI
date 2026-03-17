from engram_ai.adapters.cursor import CursorAdapter


def test_write_skills(tmp_path):
    adapter = CursorAdapter()
    path = str(tmp_path / ".cursorrules")
    adapter.write_skills(path, "- Use schema validation")
    content = (tmp_path / ".cursorrules").read_text()
    assert "# --- engram-ai:start ---" in content
    assert "Use schema validation" in content
    assert "# --- engram-ai:end ---" in content


def test_write_anti_skills(tmp_path):
    adapter = CursorAdapter()
    path = str(tmp_path / ".cursorrules")
    adapter.write_anti_skills(path, "- Never use eval()")
    content = (tmp_path / ".cursorrules").read_text()
    assert "# --- engram-ai:anti-skills:start ---" in content
    assert "Never use eval()" in content


def test_read_config(tmp_path):
    adapter = CursorAdapter()
    (tmp_path / ".cursorrules").write_text("existing rules")
    assert "existing rules" in adapter.read_config(str(tmp_path / ".cursorrules"))


def test_read_config_missing(tmp_path):
    adapter = CursorAdapter()
    assert adapter.read_config(str(tmp_path / "missing")) == ""
