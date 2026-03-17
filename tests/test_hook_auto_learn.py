import json

from click.testing import CliRunner

from engram_ai import Forge
from engram_ai.cli import main


def test_complete_pending_returns_experience(tmp_path, mock_llm):
    """complete_pending should return the recorded Experience."""
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    forge.record_pending(action="edit file", context="editing main.py")
    exp = forge.complete_pending(outcome="file saved", valence=0.8)
    assert exp is not None
    assert exp.action == "edit file"
    assert exp.outcome == "file saved"
    assert exp.valence == 0.8


def test_complete_pending_returns_none_when_no_pending(tmp_path, mock_llm):
    """complete_pending should return None when nothing is pending."""
    forge = Forge(storage_path=str(tmp_path / "data"), llm=mock_llm)
    result = forge.complete_pending(outcome="nothing", valence=0.0)
    assert result is None


def test_hook_user_prompt_submit_auto_crystallize(tmp_path, monkeypatch):
    """Hook should auto-crystallize after recording an experience."""
    storage_dir = tmp_path / "data"
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(storage_dir))

    # Pre-populate a pending experience
    forge = Forge(storage_path=str(storage_dir), llm=None)
    forge.record_pending(action="test action", context="test context")
    forge.close()

    stdin_data = json.dumps({"prompt": "perfect, thanks!"})
    runner = CliRunner()
    result = runner.invoke(main, ["hook", "user-prompt-submit"], input=stdin_data)
    # Hook should not crash
    assert result.exit_code == 0

    # Verify the experience was recorded
    forge2 = Forge(storage_path=str(storage_dir), llm=None)
    stats = forge2.status()
    assert stats["total_experiences"] >= 1
    forge2.close()


def test_hook_user_prompt_submit_no_pending(tmp_path, monkeypatch):
    """Hook should not crash when there's no pending experience."""
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    stdin_data = json.dumps({"prompt": "hello"})
    runner = CliRunner()
    result = runner.invoke(main, ["hook", "user-prompt-submit"], input=stdin_data)
    assert result.exit_code == 0


def test_hook_post_tool_use_records_pending(tmp_path, monkeypatch):
    """post-tool-use hook should record a pending experience."""
    storage_dir = tmp_path / "data"
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(storage_dir))
    stdin_data = json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": "src/main.py"},
    })
    runner = CliRunner()
    result = runner.invoke(main, ["hook", "post-tool-use"], input=stdin_data)
    assert result.exit_code == 0
    # ProjectManager stores under base_path/default/
    pending_file = storage_dir / "default" / "pending.jsonl"
    assert pending_file.exists()


def test_setup_hooks_command(tmp_path, monkeypatch):
    """setup-hooks should register hooks in Claude Code settings."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr("engram_ai.cli.Path.home", lambda: fake_home)

    runner = CliRunner()
    result = runner.invoke(main, ["setup-hooks"])
    assert result.exit_code == 0
    assert "Hooks registered" in result.output

    settings_path = fake_home / ".claude" / "settings.json"
    assert settings_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" in settings
    assert "PostToolUse" in settings["hooks"]
    assert "UserPromptSubmit" in settings["hooks"]
    # Verify engram-ai hooks are present
    post_tool_hooks = settings["hooks"]["PostToolUse"]
    assert any("engram-ai" in str(h) for h in post_tool_hooks)
    user_prompt_hooks = settings["hooks"]["UserPromptSubmit"]
    assert any("engram-ai" in str(h) for h in user_prompt_hooks)


def test_setup_hooks_idempotent(tmp_path, monkeypatch):
    """Running setup-hooks twice should not duplicate entries."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr("engram_ai.cli.Path.home", lambda: fake_home)

    runner = CliRunner()
    runner.invoke(main, ["setup-hooks"])
    runner.invoke(main, ["setup-hooks"])

    settings_path = fake_home / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    # Should have exactly 1 engram-ai entry per hook type
    post_tool = [h for h in settings["hooks"]["PostToolUse"] if "engram-ai" in str(h)]
    user_prompt = [h for h in settings["hooks"]["UserPromptSubmit"] if "engram-ai" in str(h)]
    assert len(post_tool) == 1
    assert len(user_prompt) == 1


def test_setup_hooks_preserves_existing(tmp_path, monkeypatch):
    """setup-hooks should not overwrite existing hooks."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr("engram_ai.cli.Path.home", lambda: fake_home)

    # Pre-existing settings with a custom hook
    settings_dir = fake_home / ".claude"
    settings_dir.mkdir(parents=True)
    existing = {
        "hooks": {
            "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "my-tool"}]}],
        }
    }
    (settings_dir / "settings.json").write_text(json.dumps(existing), encoding="utf-8")

    runner = CliRunner()
    runner.invoke(main, ["setup-hooks"])

    settings = json.loads((settings_dir / "settings.json").read_text(encoding="utf-8"))
    # Should have both the existing and engram-ai hooks
    assert len(settings["hooks"]["PostToolUse"]) == 2
    assert any("my-tool" in str(h) for h in settings["hooks"]["PostToolUse"])
    assert any("engram-ai" in str(h) for h in settings["hooks"]["PostToolUse"])
