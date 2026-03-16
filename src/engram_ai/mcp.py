import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from engram_ai.forge import Forge

logger = logging.getLogger(__name__)


def create_mcp_server(forge: Forge) -> Server:
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
                    },
                },
            ),
            Tool(
                name="engram_status",
                description="Show Engram-AI statistics",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
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

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.exception("MCP tool error: %s", name)
            return [TextContent(type="text", text=f"Error: {e}")]

    return server


async def run_mcp_server():
    """Run the MCP server on stdio."""
    forge = Forge()
    server = create_mcp_server(forge)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)
