import json
import logging
import os
import sys
from pathlib import Path

import click

from engram_ai.adapters import ADAPTER_REGISTRY
from engram_ai.forge import Forge
from engram_ai.project import ProjectManager

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".engram-ai"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "storage_path": str(CONFIG_DIR / "data"),
    "llm": {"provider": "claude", "model": "claude-sonnet-4-20250514"},
    "crystallize": {"min_experiences": 3, "min_confidence": 0.7},
    "evolve": {"default_config_path": "./CLAUDE.md", "strategy": "append"},
    "default_project": "default",
    "scheduler": {
        "decay_interval_hours": 6,
        "conflict_interval_hours": 12,
        "crystallize_threshold": 10,
        "enabled": True,
    },
}


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return DEFAULT_CONFIG


def _get_project_manager() -> ProjectManager:
    config = _load_config()
    base_path = Path(os.environ.get("ENGRAM_AI_STORAGE", config.get("storage_path", str(CONFIG_DIR / "data"))))
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    llm = None
    if api_key:
        from engram_ai.llm.claude import ClaudeLLM
        llm = ClaudeLLM(api_key=api_key)
    return ProjectManager(base_path=base_path, llm=llm, config=config)


def _get_forge(adapter_name="claude-code", project=None) -> Forge:
    pm = _get_project_manager()
    forge = pm.get_forge(project)
    if adapter_name != "claude-code":
        entry = ADAPTER_REGISTRY.get(adapter_name)
        if entry:
            forge._adapter = entry["class"]()
    return forge


@click.group()
@click.option("--project", "-p", default=None, help="Project name (default: from config)")
@click.pass_context
def main(ctx, project):
    """Engram-AI: Experience-driven memory for AI agents."""
    logging.basicConfig(level=logging.INFO)
    ctx.ensure_object(dict)
    ctx.obj["project"] = project


def _register_hooks(settings_path: Path) -> Path:
    """Register Engram-AI hooks in Claude Code settings. Returns the settings path."""
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = {}

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
    if not any("engram-ai" in str(h) for h in settings["hooks"]["PostToolUse"]):
        settings["hooks"]["PostToolUse"].append(engram_post_tool)

    if "UserPromptSubmit" not in settings["hooks"]:
        settings["hooks"]["UserPromptSubmit"] = []
    if not any("engram-ai" in str(h) for h in settings["hooks"]["UserPromptSubmit"]):
        settings["hooks"]["UserPromptSubmit"].append(engram_user_prompt)

    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return settings_path


@main.command("setup-hooks")
def setup_hooks():
    """Register Engram-AI hooks in Claude Code settings."""
    claude_settings_path = Path.home() / ".claude" / "settings.json"
    _register_hooks(claude_settings_path)
    click.echo(f"Hooks registered in: {claude_settings_path}")
    click.echo("Restart Claude Code to activate hooks.")


@main.command()
@click.option("--uvx", "use_uvx", is_flag=True, default=False,
              help="Configure MCP server to use uvx instead of pip-installed engram-ai.")
def setup(use_uvx: bool):
    """Auto-configure Engram-AI for Claude Code."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        click.echo(f"Created config: {CONFIG_FILE}")

    claude_settings_path = Path.home() / ".claude" / "settings.json"
    if claude_settings_path.exists():
        settings = json.loads(claude_settings_path.read_text(encoding="utf-8"))
    else:
        claude_settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = {}

    if "mcpServers" not in settings:
        settings["mcpServers"] = {}

    if use_uvx:
        settings["mcpServers"]["engram-ai"] = {
            "command": "uvx",
            "args": ["engram-ai[mcp]"],
        }
    else:
        settings["mcpServers"]["engram-ai"] = {
            "command": "engram-ai",
            "args": ["serve"],
        }

    claude_settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _register_hooks(claude_settings_path)

    click.echo(f"Updated Claude Code settings: {claude_settings_path}")
    click.echo("\nSetup complete. Restart Claude Code to activate Engram-AI.")


@main.command()
@click.pass_context
def status(ctx):
    """Show Engram-AI statistics."""
    forge = _get_forge(project=ctx.obj.get("project"))
    stats = forge.status()
    click.echo(f"Experiences: {stats['total_experiences']}")
    click.echo(f"Skills: {stats['total_skills']}")
    click.echo(f"Unapplied skills: {stats['unapplied_skills']}")


@main.command()
@click.option("--min-experiences", default=3, help="Minimum experiences for clustering")
@click.option("--min-confidence", default=0.7, help="Minimum confidence threshold")
@click.pass_context
def crystallize(ctx, min_experiences, min_confidence):
    """Crystallize skills from accumulated experiences."""
    forge = _get_forge(project=ctx.obj.get("project"))
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
@click.option("--config", "config_path", default=None, help="Config file to evolve")
@click.option("--adapter", "adapter_name", default="claude-code",
              type=click.Choice(list(ADAPTER_REGISTRY.keys())),
              help="Target framework adapter")
@click.pass_context
def evolve(ctx, config_path, adapter_name):
    """Write learned skills to agent config file."""
    if config_path is None:
        config_path = ADAPTER_REGISTRY[adapter_name]["default_config"]
    forge = _get_forge(adapter_name, project=ctx.obj.get("project"))
    record = forge.evolve(config_path=config_path)
    if record is None:
        click.echo("No unapplied skills to evolve.")
        return
    click.echo(f"Evolved: {record.diff}")
    click.echo(f"Config updated: {config_path}")


@main.command()
@click.pass_context
def decay(ctx):
    """Apply time-based confidence decay to all skills."""
    forge = _get_forge(project=ctx.obj.get("project"))
    updated = forge.apply_decay()
    if not updated:
        click.echo("No skills to decay.")
        return
    click.echo(f"Decayed {len(updated)} skill(s):")
    for skill in updated:
        click.echo(f"  - {skill.rule} (confidence: {skill.confidence:.2f})")


@main.command()
@click.pass_context
def conflicts(ctx):
    """List conflicting skill pairs."""
    forge = _get_forge(project=ctx.obj.get("project"))
    pairs = forge.detect_conflicts()
    if not pairs:
        click.echo("No conflicts detected.")
        return
    click.echo(f"{len(pairs)} conflict(s) found:")
    for a, b in pairs:
        click.echo(f"  - [{a.id[:8]}] {a.rule}")
        click.echo(f"    vs [{b.id[:8]}] {b.rule}")


@main.command()
@click.argument("id_a")
@click.argument("id_b")
@click.pass_context
def merge(ctx, id_a, id_b):
    """Auto-merge two conflicting skills."""
    forge = _get_forge(project=ctx.obj.get("project"))
    merged = forge.merge_skills(id_a, id_b)
    click.echo(f"Merged into: {merged.rule} (confidence: {merged.confidence:.2f})")


@main.command()
@click.argument("context")
@click.option("-k", default=5, help="Number of results")
@click.pass_context
def query(ctx, context, k):
    """Query past experiences for best action."""
    forge = _get_forge(project=ctx.obj.get("project"))
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
@click.pass_context
def dashboard(ctx, port, host):
    """Launch the Engram-AI web dashboard."""
    import uvicorn
    from engram_ai.dashboard.server import create_app

    pm = _get_project_manager()
    app = create_app(project_manager=pm)
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

        # Pre-emptive Warning: check for past failures with similar actions
        warnings = forge.warn(action=action, context=context)
        if warnings:
            lines = ["Warning: past issues with similar actions:"]
            for exp in warnings[:3]:
                lines.append(f'- "{exp.outcome}" (valence: {exp.valence:.1f})')
            print(json.dumps({"result": "\n".join(lines)}))
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

        experience = forge.complete_pending(
            outcome=user_message[:200],  # Truncate long messages
            valence=valence,
        )

        # Auto-learn: crystallize + evolve after every recorded experience
        if experience is not None:
            skills = forge.crystallize(min_experiences=1, min_confidence=0.5)
            if skills:
                config = _load_config()
                config_path = config.get("evolve", {}).get(
                    "default_config_path", "./CLAUDE.md"
                )
                try:
                    forge.evolve(config_path=config_path)
                except Exception:
                    pass  # Evolve failure should not block

        # Active Recall: inject relevant skills and warnings
        if user_message.strip():
            recall_result = forge._recall(user_message)
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
    except Exception:
        pass  # Hooks must never block Claude Code


@main.group()
def projects():
    """Manage projects."""
    pass


@projects.command("list")
def projects_list():
    """List all projects."""
    pm = _get_project_manager()
    names = pm.list_projects()
    if not names:
        click.echo("No projects found.")
    else:
        for name in names:
            click.echo(f"  {name}")


@projects.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
def projects_delete(name):
    """Delete a project."""
    pm = _get_project_manager()
    pm.delete_project(name)
    click.echo(f"Deleted project: {name}")
