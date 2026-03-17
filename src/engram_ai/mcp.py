import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)


def create_mcp_server(project_manager) -> Server:
    """Create an MCP server exposing Engram-AI tools."""
    server = Server("engram-ai")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="engram_record",
                description="Record an experience (action, context, outcome, valence)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "What was done"},
                        "context": {"type": "string", "description": "Situation"},
                        "outcome": {"type": "string", "description": "What happened"},
                        "valence": {
                            "type": "number",
                            "description": "Good (+1.0) to bad (-1.0)",
                            "minimum": -1.0,
                            "maximum": 1.0,
                        },
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                    "required": ["action", "context", "outcome", "valence"],
                },
            ),
            Tool(
                name="engram_query",
                description="Search past experiences for the best action in a given context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "context": {"type": "string", "description": "Current situation"},
                        "k": {"type": "integer", "description": "Number of results", "default": 5},
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                    "required": ["context"],
                },
            ),
            Tool(
                name="engram_crystallize",
                description="Extract skill patterns from accumulated experiences",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "min_experiences": {"type": "integer", "default": 3},
                        "min_confidence": {"type": "number", "default": 0.7},
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                },
            ),
            Tool(
                name="engram_evolve",
                description="Write learned skills to CLAUDE.md config file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "config_path": {
                            "type": "string",
                            "description": "Path to config file",
                            "default": "./CLAUDE.md",
                        },
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                },
            ),
            Tool(
                name="engram_status",
                description="Show Engram-AI statistics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                },
            ),
            Tool(
                name="engram_conflicts",
                description="List conflicting skill pairs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                },
            ),
            Tool(
                name="engram_merge",
                description="Merge two conflicting skills",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skill_a_id": {"type": "string"},
                        "skill_b_id": {"type": "string"},
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                    "required": ["skill_a_id", "skill_b_id"],
                },
            ),
            Tool(
                name="engram_decay",
                description="Apply time-based confidence decay",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                },
            ),
            Tool(
                name="engram_observe",
                description="Observe a conversation snippet and auto-record experiences",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant"]},
                                    "content": {"type": "string"},
                                },
                                "required": ["role", "content"],
                            },
                            "description": "Conversation history",
                        },
                        "max_turns": {
                            "type": "integer",
                            "description": "Max turn pairs to use",
                            "default": 3,
                            "minimum": 1,
                        },
                        "crystallize_threshold": {
                            "type": "integer",
                            "description": "Auto-crystallize every N experiences",
                            "default": 5,
                            "minimum": 2,
                        },
                        "project": {"type": "string", "description": "Project name (default: from config)", "default": "default"},
                    },
                    "required": ["messages"],
                },
            ),
            Tool(
                name="engram_teach",
                description="Directly teach a skill/rule to Engram-AI without going through the experience cycle",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rule": {"type": "string", "description": "The skill/rule to remember"},
                        "context_pattern": {"type": "string", "description": "When this applies"},
                        "skill_type": {
                            "type": "string",
                            "enum": ["positive", "anti"],
                            "default": "positive",
                            "description": "Skill type",
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.8,
                            "description": "Initial confidence",
                        },
                        "project": {"type": "string", "description": "Project name", "default": "default"},
                    },
                    "required": ["rule", "context_pattern"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            project = arguments.pop("project", None)
            forge = project_manager.get_forge(project)
            if name == "engram_record":
                exp = forge.record(
                    action=arguments["action"],
                    context=arguments["context"],
                    outcome=arguments["outcome"],
                    valence=arguments["valence"],
                )
                return [TextContent(type="text", text=f"Recorded experience: {exp.id}")]

            elif name == "engram_query":
                result = forge.query(
                    context=arguments["context"],
                    k=arguments.get("k", 5),
                )
                lines = []
                if result["best"]:
                    lines.append("Best actions:")
                    for exp, score in result["best"]:
                        lines.append(f"  + {exp.action} → {exp.outcome} (score: {score:.2f})")
                if result["avoid"]:
                    lines.append("Avoid:")
                    for exp, score in result["avoid"]:
                        lines.append(f"  - {exp.action} → {exp.outcome} (score: {score:.2f})")
                if not lines:
                    lines.append("No relevant experiences found.")
                return [TextContent(type="text", text="\n".join(lines))]

            elif name == "engram_crystallize":
                skills = forge.crystallize(
                    min_experiences=arguments.get("min_experiences", 3),
                    min_confidence=arguments.get("min_confidence", 0.7),
                )
                if not skills:
                    return [TextContent(type="text", text="No new skills crystallized.")]
                lines = [f"{len(skills)} skill(s) crystallized:"]
                for s in skills:
                    lines.append(f"  - {s.rule} (confidence: {s.confidence:.2f})")
                return [TextContent(type="text", text="\n".join(lines))]

            elif name == "engram_evolve":
                record = forge.evolve(
                    config_path=arguments.get("config_path", "./CLAUDE.md"),
                )
                if record is None:
                    return [TextContent(type="text", text="No unapplied skills to evolve.")]
                return [TextContent(type="text", text=f"Evolved: {record.diff}")]

            elif name == "engram_status":
                stats = forge.status()
                text = (
                    f"Experiences: {stats['total_experiences']}\n"
                    f"Skills: {stats['total_skills']}\n"
                    f"Unapplied skills: {stats['unapplied_skills']}"
                )
                return [TextContent(type="text", text=text)]

            elif name == "engram_conflicts":
                pairs = forge.detect_conflicts()
                if not pairs:
                    return [TextContent(type="text", text="No conflicts detected.")]
                lines = [f"{len(pairs)} conflict(s):"]
                for a, b in pairs:
                    lines.append(f"  [{a.id[:8]}] {a.rule} vs [{b.id[:8]}] {b.rule}")
                return [TextContent(type="text", text="\n".join(lines))]

            elif name == "engram_merge":
                merged = forge.merge_skills(arguments["skill_a_id"], arguments["skill_b_id"])
                return [TextContent(type="text", text=f"Merged: {merged.rule} (confidence: {merged.confidence:.2f})")]

            elif name == "engram_decay":
                updated = forge.apply_decay()
                if not updated:
                    return [TextContent(type="text", text="No skills to decay.")]
                return [TextContent(type="text", text=f"Decayed {len(updated)} skill(s).")]

            elif name == "engram_observe":
                result = forge.observe(
                    messages=arguments["messages"],
                    max_turns=arguments.get("max_turns", 3),
                    crystallize_threshold=arguments.get("crystallize_threshold", 5),
                )
                if result["recorded"] is None:
                    return [TextContent(type="text", text="No notable experience detected.")]
                lines = [f'Recorded: "{result["recorded"].action}" (valence: {result["recorded"].valence:.2f})']
                if result["crystallized"]:
                    lines.append(f"Auto-crystallized {len(result['crystallized'])} skill(s):")
                    for s in result["crystallized"]:
                        lines.append(f"  - {s.rule} (confidence: {s.confidence:.2f})")
                return [TextContent(type="text", text="\n".join(lines))]

            elif name == "engram_teach":
                pre_count = len(forge._storage.get_all_skills())
                skill = forge.teach(
                    rule=arguments["rule"],
                    context_pattern=arguments["context_pattern"],
                    skill_type=arguments.get("skill_type", "positive"),
                    confidence=arguments.get("confidence", 0.8),
                )
                post_count = len(forge._storage.get_all_skills())
                if post_count > pre_count:
                    text = f'Taught: "{skill.rule}" (confidence: {skill.confidence:.2f})'
                else:
                    text = f'Reinforced existing skill: "{skill.rule}" (confidence: {skill.confidence:.2f})'
                return [TextContent(type="text", text=text)]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.exception("MCP tool error: %s", name)
            return [TextContent(type="text", text=f"Error: {e}")]

    return server


async def run_mcp_server():
    """Run the MCP server on stdio."""
    import json
    import os
    from pathlib import Path
    from engram_ai.project import ProjectManager

    config_dir = Path.home() / ".engram-ai"
    config_file = config_dir / "config.json"
    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text(encoding="utf-8"))
    base_path = Path(os.environ.get("ENGRAM_AI_STORAGE", config.get("storage_path", str(config_dir / "data"))))
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    llm = None
    if api_key:
        from engram_ai.llm.claude import ClaudeLLM
        llm = ClaudeLLM(api_key=api_key)
    pm = ProjectManager(base_path=base_path, llm=llm, config=config)
    server = create_mcp_server(pm)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)
