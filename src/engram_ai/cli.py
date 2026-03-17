import json
import logging
import os
import sys
from pathlib import Path

import click

from engram_ai.forge import Forge

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".engram-ai"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "storage_path": str(CONFIG_DIR / "data"),
    "llm": {"provider": "claude", "model": "claude-sonnet-4-20250514"},
    "crystallize": {"min_experiences": 3, "min_confidence": 0.7},
    "evolve": {"default_config_path": "./CLAUDE.md", "strategy": "append"},
}


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return DEFAULT_CONFIG


def _get_forge() -> Forge:
    storage_override = os.environ.get("ENGRAM_AI_STORAGE")
    if storage_override:
        return Forge(storage_path=storage_override)
    config = _load_config()
    return Forge(storage_path=config.get("storage_path", str(CONFIG_DIR / "data")))


@click.group()
def main():
    """Engram-AI: Experience-driven memory for AI agents."""
    logging.basicConfig(level=logging.INFO)


@main.command()
def setup():
    """Auto-configure Engram-AI for Claude Code."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Write default config
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        click.echo(f"Created config: {CONFIG_FILE}")

    # Configure Claude Code settings
    claude_settings_path = Path.home() / ".claude" / "settings.json"
    if claude_settings_path.exists():
        settings = json.loads(claude_settings_path.read_text(encoding="utf-8"))
    else:
        claude_settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = {}

    # Add MCP server
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    settings["mcpServers"]["engram-ai"] = {
        "command": "engram-ai",
        "args": ["serve"],
    }

    # Add hooks (append, don't overwrite existing hooks)
    if "hooks" not in settings:
        settings["hooks"] = {}

    engram_post_tool = {
        "matcher": "*",
        "hooks": [{"type": "command", "command": "engram-ai hook post-tool-use"}],
    }
    engram_user_prompt = {
        "matcher": "",
        "hooks": [{"type": "command", "command": "engram-ai hook user-prompt-submit"}],
    }

    if "PostToolUse" not in settings["hooks"]:
        settings["hooks"]["PostToolUse"] = []
    # Only add if not already present
    if not any("engram-ai" in str(h) for h in settings["hooks"]["PostToolUse"]):
        settings["hooks"]["PostToolUse"].append(engram_post_tool)

    if "UserPromptSubmit" not in settings["hooks"]:
        settings["hooks"]["UserPromptSubmit"] = []
    if not any("engram-ai" in str(h) for h in settings["hooks"]["UserPromptSubmit"]):
        settings["hooks"]["UserPromptSubmit"].append(engram_user_prompt)

    claude_settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    click.echo(f"Updated Claude Code settings: {claude_settings_path}")
    click.echo("\nSetup complete. Restart Claude Code to activate Engram-AI.")


@main.command()
def status():
    """Show Engram-AI statistics."""
    forge = _get_forge()
    stats = forge.status()
    click.echo(f"Experiences: {stats['total_experiences']}")
    click.echo(f"Skills: {stats['total_skills']}")
    click.echo(f"Unapplied skills: {stats['unapplied_skills']}")


@main.command()
@click.option("--min-experiences", default=3, help="Minimum experiences for clustering")
@click.option("--min-confidence", default=0.7, help="Minimum confidence threshold")
def crystallize(min_experiences, min_confidence):
    """Crystallize skills from accumulated experiences."""
    forge = _get_forge()
    skills = forge.crystallize(
        min_experiences=min_experiences,
        min_confidence=min_confidence,
    )
    if not skills:
        click.echo("No new skills crystallized.")
        return
    click.echo(f"{len(skills)} skill(s) crystallized:")
    for skill in skills:
        click.echo(f"  - {skill.rule} (confidence: {skill.confidence:.2f})")


@main.command()
@click.option("--config", "config_path", default="./CLAUDE.md", help="Config file to evolve")
def evolve(config_path):
    """Write learned skills to agent config file."""
    forge = _get_forge()
    record = forge.evolve(config_path=config_path)
    if record is None:
        click.echo("No unapplied skills to evolve.")
        return
    click.echo(f"Evolved: {record.diff}")
    click.echo(f"Config updated: {config_path}")


@main.command()
@click.argument("context")
@click.option("-k", default=5, help="Number of results")
def query(context, k):
    """Query past experiences for best action."""
    forge = _get_forge()
    result = forge.query(context, k=k)

    if result["best"]:
        click.echo("Best actions:")
        for exp, score in result["best"]:
            click.echo(f"  + {exp.action} (score: {score:.2f})")

    if result["avoid"]:
        click.echo("Avoid:")
        for exp, score in result["avoid"]:
            click.echo(f"  - {exp.action} (score: {score:.2f})")

    if not result["best"] and not result["avoid"]:
        click.echo("No relevant experiences found.")


@main.command()
@click.option("--port", default=3333, help="Dashboard port")
@click.option("--host", default="127.0.0.1", help="Dashboard host")
def dashboard(port, host):
    """Launch the Engram-AI web dashboard."""
    import uvicorn
    from engram_ai.dashboard.server import create_app

    app = create_app()
    click.echo(f"Dashboard: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


@main.command()
def serve():
    """Start MCP server for Claude Code integration."""
    import asyncio

    from engram_ai.mcp import run_mcp_server

    click.echo("Starting Engram-AI MCP server...")
    asyncio.run(run_mcp_server())


@main.group()
def hook():
    """Hook commands (called by Claude Code)."""
    pass


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
    except Exception:
        pass  # Hooks must never block Claude Code


@hook.command("user-prompt-submit")
def hook_user_prompt_submit():
    """Handle UserPromptSubmit hook from Claude Code."""
    try:
        stdin_data = json.loads(sys.stdin.read())
        user_message = stdin_data.get("prompt", stdin_data.get("message", ""))

        forge = _get_forge()
        valence = forge.detect_valence(user_message)  # Tiered: keyword -> LLM -> default

        forge.complete_pending(
            outcome=user_message[:200],  # Truncate long messages
            valence=valence,
        )
    except Exception:
        pass  # Hooks must never block Claude Code
