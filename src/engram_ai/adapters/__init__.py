from engram_ai.adapters.claude_code import ClaudeCodeAdapter
from engram_ai.adapters.cursor import CursorAdapter
from engram_ai.adapters.gemini import GeminiAdapter
from engram_ai.adapters.windsurf import WindsurfAdapter

ADAPTER_REGISTRY = {
    "claude-code": {"class": ClaudeCodeAdapter, "default_config": "CLAUDE.md"},
    "cursor": {"class": CursorAdapter, "default_config": ".cursorrules"},
    "gemini": {"class": GeminiAdapter, "default_config": "GEMINI.md"},
    "windsurf": {"class": WindsurfAdapter, "default_config": ".windsurfrules"},
}
