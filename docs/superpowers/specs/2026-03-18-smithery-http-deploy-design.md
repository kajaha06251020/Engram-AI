# Smithery HTTP Deploy Design

## Goal

Publish the Engram-AI MCP server on [smithery.ai](https://smithery.ai) by adding Streamable HTTP transport and deploying to Render.

## Background

Smithery requires an HTTP URL (`smithery mcp publish <url> -n <org/server>`). The current MCP server only supports stdio transport. We need to add HTTP transport and deploy it.

## Approach

Use the existing `create_mcp_server()` which returns a low-level `Server` instance, then wrap it with `StreamableHTTPSessionManager` from the MCP Python SDK and mount it in a Starlette ASGI app.

## Changes

### 1. `src/engram_ai/mcp.py` — Add `create_http_app()` and refactor

**Refactor:** Extract `_build_project_manager()` from the duplicated logic currently in both `run_mcp_server()` and `cli.py:_get_project_manager()`. The new helper lives in `mcp.py` and `run_mcp_server()` is updated to call it.

**New function** `create_http_app()`:
1. Calls `_build_project_manager()` to get a `ProjectManager`
2. Calls `create_mcp_server(pm)` to get the `Server` with all 10 tools
3. Creates a `StreamableHTTPSessionManager(app=server)`
4. Returns a Starlette ASGI app with:
   - `POST /mcp` — MCP Streamable HTTP endpoint
   - `GET /health` — health check returning `{"status": "ok"}`

**Critical:** The MCP endpoint must use a `Route` with an ASGI class wrapper, not `Mount`. Starlette's `Mount` compiles the path as `^/mcp/(?P<path>.*)` which requires a trailing slash or sub-path, causing `POST /mcp` to return 404. Wrapping `session_manager.handle_request` in an ASGI-compatible class avoids Starlette's function introspection which would restrict methods to GET only.

```python
import contextlib
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager


class _McpHttpApp:
    """ASGI wrapper for StreamableHTTPSessionManager.handle_request."""
    def __init__(self, session_manager):
        self._sm = session_manager

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        await self._sm.handle_request(scope, receive, send)


def _build_project_manager():
    """Build a ProjectManager from config and env vars."""
    import json
    import os
    from pathlib import Path
    from engram_ai.project import ProjectManager

    config_dir = Path.home() / ".engram-ai"
    config_file = config_dir / "config.json"
    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text(encoding="utf-8"))
    base_path = Path(os.environ.get(
        "ENGRAM_AI_STORAGE",
        config.get("storage_path", str(config_dir / "data")),
    ))
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    llm = None
    if api_key:
        from engram_ai.llm.claude import ClaudeLLM
        llm = ClaudeLLM(api_key=api_key)
    return ProjectManager(base_path=base_path, llm=llm, config=config)


def create_http_app():
    """Create a Starlette ASGI app with MCP Streamable HTTP transport."""
    pm = _build_project_manager()
    server = create_mcp_server(pm)
    session_manager = StreamableHTTPSessionManager(app=server)

    async def health(request):
        return JSONResponse({"status": "ok"})

    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with session_manager.run():
            yield

    return Starlette(
        routes=[
            Route("/health", health),
            Route("/mcp", endpoint=_McpHttpApp(session_manager)),
        ],
        lifespan=lifespan,
    )
```

Also update `run_mcp_server()` to use `_build_project_manager()` instead of inline logic.

### 2. `src/engram_ai/cli.py` — Add `serve-http` command

```python
@main.command("serve-http")
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
def serve_http(host, port):
    """Start MCP server with HTTP transport (for cloud deployment)."""
    import uvicorn
    from engram_ai.mcp import create_http_app
    port = int(os.environ.get("PORT", port))
    app = create_http_app()
    uvicorn.run(app, host=host, port=port)
```

The `PORT` environment variable override ensures compatibility with Render, which injects its own port.

### 3. `pyproject.toml` — Dependencies

The `mcp>=1.0.0` package transitively depends on `starlette` and `uvicorn`. No new packages needed in `mcp` extras. However, `uvicorn[standard]` (with `uvloop` + `httptools`) is desirable for production HTTP performance, so add it explicitly:

```toml
mcp = ["mcp>=1.0.0", "uvicorn[standard]>=0.30.0"]
```

### 4. `Dockerfile` — New file

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[full]"

EXPOSE 8000
CMD ["sh", "-c", "engram-forge serve-http --host 0.0.0.0 --port ${PORT:-8000}"]
```

Uses `sh -c` to expand `$PORT` at runtime (Render injects this).

### 5. `render.yaml` — New file (Render Blueprint)

```yaml
services:
  - type: web
    name: engram-forge
    runtime: docker
    plan: free
    healthCheckPath: /health
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
```

### 6. `smithery.yaml` — Keep stdio config, add comment

The existing `smithery.yaml` with stdio + `uvx` config is kept as-is for users who install locally. The Smithery registry entry will point to the HTTP URL via the `smithery mcp publish` command, which is separate from this file.

```yaml
# Local (stdio) configuration — used when installed via uvx/pip
# HTTP endpoint published separately via: smithery mcp publish <url>
startCommand:
  type: stdio
  configSchema:
    type: object
    properties:
      storageDir:
        type: string
        title: Storage Directory
        description: "Path to store Engram data (default: ~/.engram-ai/data)"
      anthropicApiKey:
        type: string
        title: Anthropic API Key
        description: "Optional. Enables LLM-powered valence detection and crystallization."
    required: []
  commandFunction: |-
    (config) => ({
      command: "uvx",
      args: ["engram-forge[mcp]", "serve"],
      env: {
        ...(config.storageDir ? { ENGRAM_AI_STORAGE: config.storageDir } : {}),
        ...(config.anthropicApiKey ? { ANTHROPIC_API_KEY: config.anthropicApiKey } : {})
      }
    })
```

## What stays the same

- `engram-forge serve` (stdio) — unchanged, still the primary local mode
- All 10 MCP tools — unchanged, reused via `create_mcp_server()`
- `create_mcp_server()` — unchanged
- All existing tests — unchanged

## Known limitations

### Ephemeral storage on Render

Render's free tier uses ephemeral filesystem. All ChromaDB data (experiences, skills) is lost on redeploy or sleep-wake. This is acceptable for Smithery registration and demo purposes. For persistent data, users should:
- Use Engram-AI locally via `engram-forge serve` (stdio) for real work
- Upgrade to Render paid plan with persistent disk if cloud persistence is needed

### Render free tier cold starts

Auto-sleeps after 15 minutes of inactivity. Cold start takes ~30 seconds. Sufficient for Smithery registration and light usage.

## Deployment flow

1. Push changes to GitHub `main` branch
2. Create Render account → connect GitHub repo → deploy
3. Render builds Docker image, starts `engram-forge serve-http`
4. Get URL: `https://engram-forge.onrender.com`
5. Publish to Smithery:
   ```bash
   smithery auth login
   smithery mcp publish "https://engram-forge.onrender.com/mcp" -n kajaha06251020/engram-forge
   ```

## Testing

- Unit test: `create_http_app()` returns a Starlette app with correct routes
- Integration test: `httpx.AsyncClient` sends POST to `/mcp` and gets valid MCP response
- Health check test: GET `/health` returns 200 with `{"status": "ok"}`
