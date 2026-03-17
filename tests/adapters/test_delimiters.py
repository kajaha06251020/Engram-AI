from pathlib import Path
from engram_ai.adapters._delimiters import write_delimited_section, write_comment_delimited_section


def test_write_delimited_creates_new_file(tmp_path):
    path = tmp_path / "test.md"
    write_delimited_section(path, "content", "<!-- start -->", "<!-- end -->", "Title")
    text = path.read_text()
    assert "<!-- start -->" in text
    assert "content" in text
    assert "<!-- end -->" in text


def test_write_delimited_replaces_existing(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("before\n<!-- start -->\nold\n<!-- end -->\nafter\n")
    write_delimited_section(path, "new content", "<!-- start -->", "<!-- end -->", "Title")
    text = path.read_text()
    assert "new content" in text
    assert "old" not in text
    assert "before" in text
    assert "after" in text


def test_write_delimited_appends_to_existing(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("existing content\n")
    write_delimited_section(path, "skills", "<!-- start -->", "<!-- end -->", "Title")
    text = path.read_text()
    assert "existing content" in text
    assert "<!-- start -->" in text
    assert "skills" in text


def test_write_comment_delimited(tmp_path):
    path = tmp_path / ".cursorrules"
    write_comment_delimited_section(path, "rule1", "# --- start ---", "# --- end ---", "Rules")
    text = path.read_text()
    assert "# --- start ---" in text
    assert "rule1" in text
    assert "# --- end ---" in text


def test_write_comment_delimited_replaces(tmp_path):
    path = tmp_path / ".cursorrules"
    path.write_text("# --- start ---\nold\n# --- end ---\n")
    write_comment_delimited_section(path, "new", "# --- start ---", "# --- end ---", "Rules")
    text = path.read_text()
    assert "new" in text
    assert "old" not in text
