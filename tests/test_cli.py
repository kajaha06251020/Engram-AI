from click.testing import CliRunner
from engram_ai.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Engram-AI" in result.output


def test_cli_status(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    runner = CliRunner()
    result = runner.invoke(main, ["status"])
    assert "Experiences:" in result.output
    assert "Skills:" in result.output


def test_cli_crystallize_no_data(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    runner = CliRunner()
    result = runner.invoke(main, ["crystallize"])
    assert result.exit_code == 0
    assert "No new skills" in result.output


def test_cli_query(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    runner = CliRunner()
    result = runner.invoke(main, ["query", "test context"])
    assert result.exit_code == 0
    assert "No relevant experiences found." in result.output


def test_decay_command(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    runner = CliRunner()
    result = runner.invoke(main, ["decay"])
    assert result.exit_code == 0


def test_conflicts_command(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    runner = CliRunner()
    result = runner.invoke(main, ["conflicts"])
    assert result.exit_code == 0
    assert "No conflicts" in result.output


def test_evolve_with_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path / "data"))
    runner = CliRunner()
    result = runner.invoke(main, ["evolve", "--adapter", "cursor"])
    assert result.exit_code == 0


def test_projects_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(main, ["projects", "list"])
    assert result.exit_code == 0


def test_projects_list_with_data(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGRAM_AI_STORAGE", str(tmp_path))
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()
    runner = CliRunner()
    result = runner.invoke(main, ["projects", "list"])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output


def test_setup_uvx_flag_writes_uvx_config(tmp_path, monkeypatch):
    """setup --uvx writes uvx-based MCP server config."""
    from click.testing import CliRunner
    from engram_ai.cli import main
    import json

    fake_settings = tmp_path / ".claude" / "settings.json"
    fake_settings.parent.mkdir(parents=True)
    fake_config_dir = tmp_path / ".engram-ai"

    monkeypatch.setattr("engram_ai.cli.CONFIG_DIR", fake_config_dir)
    monkeypatch.setattr("engram_ai.cli.CONFIG_FILE", fake_config_dir / "config.json")

    import pathlib
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--uvx"])
    assert result.exit_code == 0, result.output

    settings = json.loads(fake_settings.read_text())
    mcp = settings["mcpServers"]["engram-forge"]
    assert mcp["command"] == "uvx"
    assert "engram-forge[mcp]" in mcp["args"]


def test_setup_default_writes_engram_serve_config(tmp_path, monkeypatch):
    """setup (no flags) writes engram-ai serve config."""
    from click.testing import CliRunner
    from engram_ai.cli import main
    import json

    fake_settings = tmp_path / ".claude" / "settings.json"
    fake_settings.parent.mkdir(parents=True)
    fake_config_dir = tmp_path / ".engram-ai"

    monkeypatch.setattr("engram_ai.cli.CONFIG_DIR", fake_config_dir)
    monkeypatch.setattr("engram_ai.cli.CONFIG_FILE", fake_config_dir / "config.json")

    import pathlib
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["setup"])
    assert result.exit_code == 0, result.output

    settings = json.loads(fake_settings.read_text())
    mcp = settings["mcpServers"]["engram-forge"]
    assert mcp["command"] == "engram-forge"
    assert mcp["args"] == ["serve"]
