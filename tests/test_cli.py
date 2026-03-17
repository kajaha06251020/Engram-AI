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
