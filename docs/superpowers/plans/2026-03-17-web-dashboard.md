# Web Dashboard Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time web dashboard (FastAPI + Next.js SPA) for visualizing Engram-AI experiences, skills, and neural graph.

**Architecture:** FastAPI serves REST API + WebSocket + static Next.js export. Forge singleton is created via config resolution (same as CLI). WebSocket bridges sync EventBus to async via `asyncio.Queue` with `call_soon_threadsafe`. Next.js is statically exported and committed to git — users don't need Node.js.

**Tech Stack:** Python (FastAPI, uvicorn), TypeScript (Next.js 14, React 18, Tailwind 3, Recharts, react-force-graph-2d, framer-motion 11)

**Spec:** `docs/specs/2026-03-17-engram-ai-dashboard-design.md`

---

## File Structure

### Backend (Python)

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/engram_ai/dashboard/__init__.py` | Package marker |
| Create | `src/engram_ai/dashboard/server.py` | `create_app()` factory, Forge singleton, CORS, static mount |
| Create | `src/engram_ai/dashboard/api.py` | All REST endpoints + WebSocket endpoint |
| Modify | `src/engram_ai/cli.py` | Add `dashboard` command |
| Modify | `pyproject.toml` | Add `fastapi`, `uvicorn[standard]` dependencies |

### Backend Tests

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `tests/dashboard/__init__.py` | Package marker |
| Create | `tests/dashboard/test_api.py` | REST endpoint tests |
| Create | `tests/dashboard/test_websocket.py` | WebSocket event delivery + cleanup tests |

### Frontend (TypeScript/React)

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `dashboard/package.json` | Dependencies + scripts |
| Create | `dashboard/next.config.mjs` | Static export config |
| Create | `dashboard/tailwind.config.ts` | Custom Engram-AI theme |
| Create | `dashboard/postcss.config.mjs` | PostCSS + Tailwind |
| Create | `dashboard/tsconfig.json` | TypeScript config |
| Create | `dashboard/src/lib/types.ts` | Shared TypeScript interfaces |
| Create | `dashboard/src/hooks/useApi.ts` | REST API fetch hook |
| Create | `dashboard/src/hooks/useWebSocket.ts` | WebSocket connection hook |
| Create | `dashboard/src/app/globals.css` | Tailwind directives + font import |
| Create | `dashboard/src/app/layout.tsx` | Root layout with nav header |
| Create | `dashboard/src/app/page.tsx` | Overview page |
| Create | `dashboard/src/app/experiences/page.tsx` | Experiences table page |
| Create | `dashboard/src/app/skills/page.tsx` | Skills card grid page |
| Create | `dashboard/src/app/graph/page.tsx` | Neural graph page |
| Create | `dashboard/src/components/NavTabs.tsx` | Top tab navigation |
| Create | `dashboard/src/components/StatsCards.tsx` | Stats cards row |
| Create | `dashboard/src/components/ValenceTrend.tsx` | Valence area chart |
| Create | `dashboard/src/components/MiniGraph.tsx` | Mini graph preview |
| Create | `dashboard/src/components/RecentExperiences.tsx` | Recent experiences list |

### Build Integration

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/engram_ai/dashboard/static/.gitkeep` | Placeholder for built files |
| Modify | `pyproject.toml` | Include static files in wheel |

---

## Chunk 1: Backend

### Task 1: Python Dependencies + Dashboard Package

**Files:**
- Modify: `pyproject.toml`
- Create: `src/engram_ai/dashboard/__init__.py`
- Create: `tests/dashboard/__init__.py`
- Create: `src/engram_ai/dashboard/static/.gitkeep`

- [ ] **Step 1: Add FastAPI and uvicorn to pyproject.toml dependencies**

In `pyproject.toml`, add to the `dependencies` list:

```toml
"fastapi>=0.115.0",
"uvicorn[standard]>=0.30.0",
```

Also add `httpx` to the dev dependencies (required by FastAPI's `TestClient`):

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 2: Create dashboard package and test directory**

Create empty `__init__.py` files:

```
src/engram_ai/dashboard/__init__.py  (empty)
tests/dashboard/__init__.py          (empty)
src/engram_ai/dashboard/static/.gitkeep  (empty)
```

- [ ] **Step 3: Install updated dependencies**

Run: `pip install -e ".[dev]"`
Expected: Successfully installs fastapi and uvicorn

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml src/engram_ai/dashboard/__init__.py tests/dashboard/__init__.py src/engram_ai/dashboard/static/.gitkeep
git commit -m "feat(dashboard): add FastAPI/uvicorn deps and package skeleton"
```

---

### Task 2: FastAPI Server Factory + REST API Endpoints

**Files:**
- Create: `src/engram_ai/dashboard/server.py`
- Create: `src/engram_ai/dashboard/api.py`

- [ ] **Step 1: Write tests for all REST endpoints**

Create `tests/dashboard/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient

from engram_ai import Forge
from engram_ai.dashboard.server import create_app
from engram_ai.models.skill import Skill


@pytest.fixture
def forge(tmp_path, mock_llm):
    return Forge(storage_path=str(tmp_path / "test_db"), llm=mock_llm)


@pytest.fixture
def client(forge):
    app = create_app(forge=forge)
    return TestClient(app)


@pytest.fixture
def seeded_forge(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "test_db"), llm=mock_llm)
    exp1 = forge.record(
        action="Used list comprehension",
        context="Data processing",
        outcome="Fast and readable",
        valence=0.9,
    )
    forge.record(
        action="Skipped type hints",
        context="Utility functions",
        outcome="Hard to maintain",
        valence=-0.7,
    )
    exp3 = forge.record(
        action="Added tests first",
        context="New feature",
        outcome="Caught bugs early",
        valence=0.8,
    )
    skill = Skill(
        rule="Prefer list comprehensions for data transforms",
        context_pattern="Data processing",
        confidence=0.85,
        source_experiences=[exp1.id, exp3.id],
        evidence_count=2,
        valence_summary={"positive": 2, "negative": 0},
    )
    forge._storage.store_skill(skill)
    return forge


@pytest.fixture
def seeded_client(seeded_forge):
    app = create_app(forge=seeded_forge)
    return TestClient(app)


def test_status_returns_counts(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert data["total_experiences"] == 0
    assert data["total_skills"] == 0
    assert data["unapplied_skills"] == 0


def test_status_reflects_data(seeded_client):
    data = seeded_client.get("/api/status").json()
    assert data["total_experiences"] == 3
    assert data["total_skills"] == 1


def test_experiences_empty(client):
    r = client.get("/api/experiences")
    assert r.status_code == 200
    assert r.json() == []


def test_experiences_returns_all(seeded_client):
    data = seeded_client.get("/api/experiences").json()
    assert len(data) == 3


def test_search_returns_best_and_avoid(seeded_client):
    r = seeded_client.get("/api/experiences/search?q=data+processing")
    assert r.status_code == 200
    data = r.json()
    assert "best" in data
    assert "avoid" in data
    for item in data["best"] + data["avoid"]:
        assert "experience" in item
        assert "score" in item


def test_skills_returns_with_applied_status(seeded_client):
    data = seeded_client.get("/api/skills").json()
    assert len(data) == 1
    assert "applied" in data[0]
    assert data[0]["applied"] is False


def test_graph_returns_nodes_and_edges(seeded_client):
    data = seeded_client.get("/api/graph").json()
    assert "nodes" in data
    assert "edges" in data
    node_types = {n["type"] for n in data["nodes"]}
    assert "experience" in node_types
    assert "skill" in node_types


def test_crystallize_returns_list(seeded_client):
    r = seeded_client.post("/api/crystallize", json={})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_evolve_returns_record_or_null(seeded_client):
    r = seeded_client.post("/api/evolve", json={"config_path": "./test_CLAUDE.md"})
    assert r.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/dashboard/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engram_ai.dashboard.server'`

- [ ] **Step 3: Create api.py with all endpoints**

Create `src/engram_ai/dashboard/api.py`:

```python
"""REST API and WebSocket endpoints for Engram-AI dashboard."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.requests import Request

from engram_ai.events.events import (
    AGENT_EVOLVED,
    EXPERIENCE_PENDING,
    EXPERIENCE_RECORDED,
    SKILL_CRYSTALLIZED,
)
from engram_ai.forge import Forge

router = APIRouter(prefix="/api")


def get_forge(request: Request) -> Forge:
    return request.app.state.forge


# --- Request schemas ---


class CrystallizeRequest(BaseModel):
    min_experiences: int = 3
    min_confidence: float = 0.7


class EvolveRequest(BaseModel):
    config_path: str = "./CLAUDE.md"


# --- GET endpoints ---


@router.get("/status")
async def get_status(forge: Forge = Depends(get_forge)) -> dict:
    return forge.status()


@router.get("/experiences")
async def get_experiences(forge: Forge = Depends(get_forge)) -> list[dict]:
    experiences = forge._storage.get_all_experiences()
    return [exp.model_dump() for exp in experiences]


@router.get("/experiences/search")
async def search_experiences(
    q: str, k: int = 5, forge: Forge = Depends(get_forge)
) -> dict:
    result = forge.query(q, k)
    return {
        "best": [
            {"experience": exp.model_dump(), "score": round(score, 4)}
            for exp, score in result.best
        ],
        "avoid": [
            {"experience": exp.model_dump(), "score": round(score, 4)}
            for exp, score in result.avoid
        ],
    }


@router.get("/skills")
async def get_skills(forge: Forge = Depends(get_forge)) -> list[dict]:
    all_skills = forge._storage.get_all_skills()
    unapplied = forge._storage.get_unapplied_skills()
    unapplied_ids = {s.id for s in unapplied}
    return [
        {**skill.model_dump(), "applied": skill.id not in unapplied_ids}
        for skill in all_skills
    ]


@router.get("/graph")
async def get_graph(forge: Forge = Depends(get_forge)) -> dict:
    storage = forge._storage
    experiences = storage.get_all_experiences()
    skills = storage.get_all_skills()

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for exp in experiences:
        nodes.append(
            {
                "id": exp.id,
                "type": "experience",
                "label": exp.action[:80],
                "valence": exp.valence,
                "timestamp": exp.timestamp.isoformat(),
            }
        )

    for skill in skills:
        nodes.append(
            {
                "id": skill.id,
                "type": "skill",
                "label": skill.rule[:80],
                "confidence": skill.confidence,
            }
        )

    for skill in skills:
        for exp_id in skill.source_experiences:
            edges.append({"source": exp_id, "target": skill.id, "type": "source"})

    seen_pairs: set[tuple[str, str]] = set()
    for exp in experiences:
        similar = storage.query_experiences(exp.action, k=5)
        for other_exp, score in similar:
            if other_exp.id == exp.id or score <= 0.3:
                continue
            pair = tuple(sorted([exp.id, other_exp.id]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            edges.append(
                {
                    "source": exp.id,
                    "target": other_exp.id,
                    "type": "similarity",
                    "weight": round(score, 3),
                }
            )

    return {"nodes": nodes, "edges": edges}


# --- POST endpoints ---


@router.post("/crystallize")
async def crystallize(
    body: CrystallizeRequest, forge: Forge = Depends(get_forge)
) -> list[dict]:
    skills = forge.crystallize(
        min_experiences=body.min_experiences,
        min_confidence=body.min_confidence,
    )
    return [skill.model_dump() for skill in skills]


@router.post("/evolve")
async def evolve(body: EvolveRequest, forge: Forge = Depends(get_forge)):
    record = forge.evolve(config_path=body.config_path)
    return record.model_dump() if record else None


# --- WebSocket ---


ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    forge: Forge = websocket.app.state.forge
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def on_event(event_name: str):
        def handler(payload):
            data = {"event": event_name, "data": payload.model_dump()}
            loop.call_soon_threadsafe(queue.put_nowait, data)

        return handler

    handlers = {}
    for event in [
        EXPERIENCE_RECORDED,
        EXPERIENCE_PENDING,
        SKILL_CRYSTALLIZED,
        AGENT_EVOLVED,
    ]:
        h = on_event(event)
        forge._event_bus.on(event, h)
        handlers[event] = h

    try:
        while True:
            data = await queue.get()
            await websocket.send_json(data)
    except WebSocketDisconnect:
        pass
    finally:
        for event, h in handlers.items():
            forge._event_bus.off(event, h)
```

- [ ] **Step 4: Create server.py with app factory**

Create `src/engram_ai/dashboard/server.py`:

```python
"""FastAPI application factory for Engram-AI dashboard."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from engram_ai.dashboard.api import router, ws_router
from engram_ai.forge import Forge

CONFIG_DIR = Path.home() / ".engram-ai"
CONFIG_FILE = CONFIG_DIR / "config.json"


def create_app(forge: Forge | None = None) -> FastAPI:
    """Create and configure the dashboard FastAPI application.

    Args:
        forge: Optional pre-configured Forge instance (for testing).
               If None, creates one from environment/config.
    """
    app = FastAPI(title="Engram-AI Dashboard")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3333"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if forge is None:
        storage_override = os.environ.get("ENGRAM_AI_STORAGE")
        if storage_override:
            forge = Forge(storage_path=storage_override)
        elif CONFIG_FILE.exists():
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            forge = Forge(
                storage_path=config.get("storage_path", str(CONFIG_DIR / "data"))
            )
        else:
            forge = Forge()

    app.state.forge = forge

    app.include_router(router)
    app.include_router(ws_router)

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists() and any(static_dir.iterdir()):
        app.mount(
            "/", StaticFiles(directory=str(static_dir), html=True), name="static"
        )

    return app
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/dashboard/test_api.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/engram_ai/dashboard/server.py src/engram_ai/dashboard/api.py tests/dashboard/test_api.py
git commit -m "feat(dashboard): add FastAPI server factory and REST API endpoints"
```

---

### Task 3: WebSocket Tests

**Files:**
- Create: `tests/dashboard/test_websocket.py`

- [ ] **Step 1: Write WebSocket tests**

Create `tests/dashboard/test_websocket.py`:

```python
import pytest
from fastapi.testclient import TestClient

from engram_ai import Forge
from engram_ai.dashboard.server import create_app


@pytest.fixture
def forge(tmp_path, mock_llm):
    return Forge(storage_path=str(tmp_path / "test_db"), llm=mock_llm)


@pytest.fixture
def client(forge):
    app = create_app(forge=forge)
    return TestClient(app)


def test_websocket_receives_experience_event(client, forge):
    """Recording an experience pushes event to connected WebSocket."""
    with client.websocket_connect("/ws") as ws:
        forge.record(
            action="Test action",
            context="Test context",
            outcome="Test outcome",
            valence=0.5,
        )
        data = ws.receive_json()
        assert data["event"] == "experience.recorded"
        assert data["data"]["action"] == "Test action"


def test_websocket_disconnect_cleans_up_handlers(client, forge):
    """Disconnecting removes EventBus listeners."""
    initial = len(forge._event_bus._subscribers.get("experience.recorded", []))
    with client.websocket_connect("/ws"):
        pass
    current = len(forge._event_bus._subscribers.get("experience.recorded", []))
    assert current == initial
```

- [ ] **Step 2: Run WebSocket tests**

Run: `python -m pytest tests/dashboard/test_websocket.py -v`
Expected: All tests PASS (implementation already in api.py from Task 2)

- [ ] **Step 3: Commit**

```bash
git add tests/dashboard/test_websocket.py
git commit -m "test(dashboard): add WebSocket event delivery and cleanup tests"
```

---

### Task 4: CLI Dashboard Command

**Files:**
- Modify: `src/engram_ai/cli.py`

- [ ] **Step 1: Add the dashboard command to cli.py**

Add after the existing commands in `src/engram_ai/cli.py`:

```python
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
```

- [ ] **Step 2: Verify CLI command registers**

Run: `engram-ai dashboard --help`
Expected: Shows help with `--port` and `--host` options

- [ ] **Step 3: Run all backend tests**

Run: `python -m pytest tests/ -v`
Expected: All tests pass (existing + new dashboard tests)

- [ ] **Step 4: Commit**

```bash
git add src/engram_ai/cli.py
git commit -m "feat(dashboard): add CLI 'dashboard' command with --port/--host"
```

---

## Chunk 2: Frontend Foundation

### Task 5: Next.js Project Scaffold

**Files:**
- Create: `dashboard/package.json`
- Create: `dashboard/next.config.mjs`
- Create: `dashboard/tailwind.config.ts`
- Create: `dashboard/postcss.config.mjs`
- Create: `dashboard/tsconfig.json`

- [ ] **Step 1: Create package.json**

Create `dashboard/package.json`:

```json
{
  "name": "engram-ai-dashboard",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --port 3000",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "recharts": "^2.12.0",
    "react-force-graph-2d": "^1.25.0",
    "framer-motion": "^11.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.3.0",
    "@types/node": "^22.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

- [ ] **Step 2: Create next.config.mjs**

Create `dashboard/next.config.mjs`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
```

- [ ] **Step 3: Create tailwind.config.ts**

Create `dashboard/tailwind.config.ts`:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        engram: {
          bg: "#0f0f23",
          card: "#1a1a3e",
          border: "#2a2a4e",
          purple: { DEFAULT: "#818cf8", light: "#a78bfa" },
          green: { DEFAULT: "#34d399", light: "#6ee7b7" },
          red: { DEFAULT: "#f87171", light: "#fca5a5" },
          amber: { DEFAULT: "#fbbf24", light: "#fcd34d" },
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 4: Create postcss.config.mjs**

Create `dashboard/postcss.config.mjs`:

```javascript
/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;
```

- [ ] **Step 5: Create tsconfig.json**

Create `dashboard/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": { "@/*": ["./src/*"] },
    "plugins": [{ "name": "next" }]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 6: Add dashboard ignores to .gitignore**

Append to the project root `.gitignore`:

```
# Dashboard frontend
dashboard/node_modules/
dashboard/.next/
dashboard/out/
```

- [ ] **Step 7: Install dependencies**

Run: `cd dashboard && npm install`
Expected: `node_modules/` created, no peer dependency errors

- [ ] **Step 8: Commit**

```bash
git add dashboard/package.json dashboard/next.config.mjs dashboard/tailwind.config.ts dashboard/postcss.config.mjs dashboard/tsconfig.json dashboard/package-lock.json .gitignore
git commit -m "feat(dashboard): scaffold Next.js 14 project with Tailwind 3"
```

---

### Task 6: TypeScript Types + API/WebSocket Hooks

**Files:**
- Create: `dashboard/src/lib/types.ts`
- Create: `dashboard/src/hooks/useApi.ts`
- Create: `dashboard/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Create TypeScript type definitions**

Create `dashboard/src/lib/types.ts`:

```typescript
export interface Experience {
  id: string;
  schema_version: number;
  action: string;
  context: string;
  outcome: string;
  valence: number;
  timestamp: string;
  metadata: Record<string, unknown>;
  status: string;
}

export interface Skill {
  id: string;
  schema_version: number;
  rule: string;
  context_pattern: string;
  confidence: number;
  source_experiences: string[];
  evidence_count: number;
  valence_summary: { positive: number; negative: number };
  created_at: string;
  applied: boolean;
}

export interface Status {
  total_experiences: number;
  total_skills: number;
  unapplied_skills: number;
}

export interface GraphNode {
  id: string;
  type: "experience" | "skill";
  label: string;
  valence?: number;
  confidence?: number;
  timestamp?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: "source" | "similarity";
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchResult {
  best: Array<{ experience: Experience; score: number }>;
  avoid: Array<{ experience: Experience; score: number }>;
}
```

- [ ] **Step 2: Create useApi hook**

Create `dashboard/src/hooks/useApi.ts`:

```typescript
"use client";

import { useState, useEffect, useCallback } from "react";

export function useApi<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(path);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch, setData };
}

export async function postApi<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `API error: ${res.status}`);
  }
  return res.json();
}
```

- [ ] **Step 3: Create useWebSocket hook**

Create `dashboard/src/hooks/useWebSocket.ts`:

```typescript
"use client";

import { useEffect, useRef, useCallback } from "react";

type EventHandler = (data: unknown) => void;

export function useWebSocket(handlers: Record<string, EventHandler>) {
  const wsRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;
  const retriesRef = useRef(0);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      retriesRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const handler = handlersRef.current[msg.event];
        if (handler) handler(msg.data);
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (retriesRef.current < 5) {
        const delay = Math.min(1000 * 2 ** retriesRef.current, 30000);
        retriesRef.current++;
        setTimeout(connect, delay);
      }
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);
}
```

- [ ] **Step 4: Commit**

```bash
git add dashboard/src/lib/types.ts dashboard/src/hooks/useApi.ts dashboard/src/hooks/useWebSocket.ts
git commit -m "feat(dashboard): add TypeScript types and API/WebSocket hooks"
```

---

### Task 7: Root Layout + NavTabs + Global Styles

**Files:**
- Create: `dashboard/src/app/globals.css`
- Create: `dashboard/src/app/layout.tsx`
- Create: `dashboard/src/components/NavTabs.tsx`

- [ ] **Step 1: Create globals.css**

Create `dashboard/src/app/globals.css`:

```css
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap");

@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  -webkit-font-smoothing: antialiased;
}
```

- [ ] **Step 2: Create NavTabs component**

Create `dashboard/src/components/NavTabs.tsx`:

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", label: "Overview" },
  { href: "/experiences", label: "Experiences" },
  { href: "/skills", label: "Skills" },
  { href: "/graph", label: "Graph" },
];

export default function NavTabs() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-6">
      {tabs.map((tab) => {
        const active =
          tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`text-sm py-1 border-b-2 transition-colors ${
              active
                ? "text-engram-purple border-engram-purple"
                : "text-gray-500 border-transparent hover:text-gray-300"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
```

- [ ] **Step 3: Create root layout**

Create `dashboard/src/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import "./globals.css";
import NavTabs from "@/components/NavTabs";

export const metadata: Metadata = {
  title: "Engram-AI Dashboard",
  description: "Real-time visualization of AI agent experiences and skills",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-engram-bg text-gray-200 min-h-screen font-sans">
        <header className="border-b border-engram-border px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-engram-purple to-purple-400" />
              <span className="font-bold text-sm">Engram-AI</span>
            </div>
            <NavTabs />
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-6">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 4: Verify dev server starts**

Run: `cd dashboard && npm run dev`
Expected: Next.js dev server starts on port 3000, no compilation errors

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/app/globals.css dashboard/src/app/layout.tsx dashboard/src/components/NavTabs.tsx
git commit -m "feat(dashboard): add root layout with dark theme and tab navigation"
```

---

### Task 8: Overview Page + Components

**Files:**
- Create: `dashboard/src/components/StatsCards.tsx`
- Create: `dashboard/src/components/ValenceTrend.tsx`
- Create: `dashboard/src/components/MiniGraph.tsx`
- Create: `dashboard/src/components/RecentExperiences.tsx`
- Create: `dashboard/src/app/page.tsx`

- [ ] **Step 1: Create StatsCards component**

Create `dashboard/src/components/StatsCards.tsx`:

```tsx
"use client";

import { motion } from "framer-motion";
import { Status } from "@/lib/types";

const cards = [
  {
    key: "experiences",
    label: "Experiences",
    field: "total_experiences" as const,
    color: "text-engram-purple-light",
    bg: "bg-engram-purple/10",
  },
  {
    key: "skills",
    label: "Skills",
    field: "total_skills" as const,
    color: "text-engram-green-light",
    bg: "bg-engram-green/10",
  },
  {
    key: "unapplied",
    label: "Unapplied",
    field: "unapplied_skills" as const,
    color: "text-engram-amber-light",
    bg: "bg-engram-amber/10",
  },
];

export default function StatsCards({ status }: { status: Status | null }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {cards.map((card, i) => (
        <motion.div
          key={card.key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className={`rounded-xl ${card.bg} border border-engram-border p-6 text-center`}
        >
          <div
            className={`text-xs uppercase tracking-wider ${card.color} opacity-80`}
          >
            {card.label}
          </div>
          <div className={`text-4xl font-bold mt-2 ${card.color}`}>
            {status?.[card.field] ?? 0}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create ValenceTrend component**

Create `dashboard/src/components/ValenceTrend.tsx`:

```tsx
"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Experience } from "@/lib/types";

export default function ValenceTrend({
  experiences,
}: {
  experiences: Experience[];
}) {
  const data = [...experiences]
    .sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
    .map((exp) => ({
      time: new Date(exp.timestamp).toLocaleDateString(),
      positive: exp.valence >= 0 ? exp.valence : 0,
      negative: exp.valence < 0 ? exp.valence : 0,
    }));

  return (
    <div className="rounded-xl bg-engram-card border border-engram-border p-4 h-full">
      <h3 className="text-xs uppercase tracking-wider text-engram-purple opacity-80 mb-4">
        Valence Trend
      </h3>
      {data.length === 0 ? (
        <div className="text-sm text-gray-500 flex items-center justify-center h-48">
          No data
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="posGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#34d399" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="negGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f87171" stopOpacity={0} />
                <stop offset="100%" stopColor="#f87171" stopOpacity={0.3} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              stroke="#2a2a4e"
            />
            <YAxis
              domain={[-1, 1]}
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              stroke="#2a2a4e"
            />
            <Tooltip
              contentStyle={{
                background: "#1a1a3e",
                border: "1px solid #2a2a4e",
                borderRadius: 8,
              }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Area
              type="monotone"
              dataKey="positive"
              stroke="#34d399"
              fill="url(#posGrad)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="negative"
              stroke="#f87171"
              fill="url(#negGrad)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create MiniGraph component**

Create `dashboard/src/components/MiniGraph.tsx`:

```tsx
"use client";

import { motion } from "framer-motion";
import { GraphData } from "@/lib/types";
import Link from "next/link";

export default function MiniGraph({ graph }: { graph: GraphData | null }) {
  const nodes = graph?.nodes.slice(0, 20) ?? [];

  return (
    <Link href="/graph" className="block">
      <div className="rounded-xl bg-engram-card border border-engram-border p-4 h-full hover:border-engram-purple/50 transition-colors cursor-pointer">
        <h3 className="text-xs uppercase tracking-wider text-engram-purple opacity-80 mb-4">
          Neural Graph
        </h3>
        <div className="flex items-center justify-center h-48">
          {nodes.length === 0 ? (
            <div className="text-sm text-gray-500">No data</div>
          ) : (
            <svg viewBox="0 0 200 150" className="w-full h-full">
              {nodes.map((node, i) => {
                const angle = (2 * Math.PI * i) / nodes.length;
                const cx = 100 + 60 * Math.cos(angle);
                const cy = 75 + 45 * Math.sin(angle);
                const fill =
                  node.type === "skill"
                    ? "#fbbf24"
                    : (node.valence ?? 0) >= 0
                      ? "#34d399"
                      : "#f87171";
                const r =
                  node.type === "skill"
                    ? 6
                    : 4 + Math.abs(node.valence ?? 0) * 4;
                return (
                  <motion.circle
                    key={node.id}
                    cx={cx}
                    cy={cy}
                    r={r}
                    fill={fill}
                    opacity={0.8}
                    animate={{ r: [r, r + 1.5, r] }}
                    transition={{
                      duration: 2 + i * 0.3,
                      repeat: Infinity,
                    }}
                  />
                );
              })}
            </svg>
          )}
        </div>
        <div className="text-center text-xs text-gray-500 mt-2">
          Click to explore
        </div>
      </div>
    </Link>
  );
}
```

- [ ] **Step 4: Create RecentExperiences component**

Create `dashboard/src/components/RecentExperiences.tsx`:

```tsx
"use client";

import { motion } from "framer-motion";
import { Experience } from "@/lib/types";

function valenceColor(v: number): string {
  if (v >= 0.5) return "text-engram-green";
  if (v > 0) return "text-engram-green opacity-60";
  if (v > -0.5) return "text-engram-red opacity-60";
  return "text-engram-red";
}

export default function RecentExperiences({
  experiences,
}: {
  experiences: Experience[];
}) {
  const recent = [...experiences]
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
    .slice(0, 10);

  return (
    <div className="rounded-xl bg-engram-card border border-engram-border p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-xs uppercase tracking-wider text-engram-green opacity-80">
          Recent Experiences
        </h3>
        <a
          href="/experiences"
          className="text-xs text-gray-500 hover:text-gray-300"
        >
          View All
        </a>
      </div>
      {recent.length === 0 ? (
        <div className="text-sm text-gray-500">
          No experiences recorded yet.
        </div>
      ) : (
        <div className="space-y-2">
          {recent.map((exp, i) => (
            <motion.div
              key={exp.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex justify-between items-center py-1.5 border-l-2 pl-3"
              style={{
                borderColor: exp.valence >= 0 ? "#34d399" : "#f87171",
              }}
            >
              <span className="text-sm text-gray-300 truncate mr-4">
                {exp.action}
              </span>
              <span className={`text-sm font-mono ${valenceColor(exp.valence)}`}>
                {exp.valence > 0 ? "+" : ""}
                {exp.valence.toFixed(1)}
              </span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Create Overview page**

Create `dashboard/src/app/page.tsx`:

```tsx
"use client";

import { useApi } from "@/hooks/useApi";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Status, Experience, GraphData } from "@/lib/types";
import StatsCards from "@/components/StatsCards";
import ValenceTrend from "@/components/ValenceTrend";
import MiniGraph from "@/components/MiniGraph";
import RecentExperiences from "@/components/RecentExperiences";

export default function OverviewPage() {
  const { data: status, setData: setStatus } = useApi<Status>("/api/status");
  const { data: experiences, setData: setExperiences } =
    useApi<Experience[]>("/api/experiences");
  const { data: graph } = useApi<GraphData>("/api/graph");

  useWebSocket({
    "experience.recorded": (data) => {
      const exp = data as Experience;
      setExperiences((prev) => (prev ? [exp, ...prev] : [exp]));
      setStatus((prev) =>
        prev
          ? { ...prev, total_experiences: prev.total_experiences + 1 }
          : prev
      );
    },
    "skill.crystallized": () => {
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              total_skills: prev.total_skills + 1,
              unapplied_skills: prev.unapplied_skills + 1,
            }
          : prev
      );
    },
  });

  return (
    <div className="space-y-6">
      <StatsCards status={status} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ValenceTrend experiences={experiences ?? []} />
        <MiniGraph graph={graph} />
      </div>
      <RecentExperiences experiences={experiences ?? []} />
    </div>
  );
}
```

- [ ] **Step 6: Verify dev server renders Overview page**

Run: `cd dashboard && npm run dev`
Expected: Page renders at http://localhost:3000 with no errors. Shows "No data" states.

- [ ] **Step 7: Commit**

```bash
git add dashboard/src/components/ dashboard/src/app/page.tsx
git commit -m "feat(dashboard): add Overview page with stats, valence trend, mini graph, recent experiences"
```

---

## Chunk 3: Feature Pages + Build Pipeline

### Task 9: Experiences Page

**Files:**
- Create: `dashboard/src/app/experiences/page.tsx`

- [ ] **Step 1: Create Experiences page**

Create `dashboard/src/app/experiences/page.tsx`:

```tsx
"use client";

import React, { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Experience, SearchResult } from "@/lib/types";

function valenceBadge(v: number) {
  const color =
    v >= 0.5
      ? "bg-engram-green/20 text-engram-green"
      : v > 0
        ? "bg-engram-green/10 text-engram-green/60"
        : v > -0.5
          ? "bg-engram-red/10 text-engram-red/60"
          : "bg-engram-red/20 text-engram-red";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono ${color}`}>
      {v > 0 ? "+" : ""}
      {v.toFixed(2)}
    </span>
  );
}

export default function ExperiencesPage() {
  const { data: experiences, setData: setExperiences } =
    useApi<Experience[]>("/api/experiences");
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [filter, setFilter] = useState<
    "all" | "positive" | "negative" | "pending"
  >("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [sortBy, setSortBy] = useState<"timestamp" | "valence">("timestamp");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useWebSocket({
    "experience.recorded": (data) => {
      setExperiences((prev) =>
        prev ? [data as Experience, ...prev] : [data as Experience]
      );
    },
  });

  const handleSearch = async () => {
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const res = await fetch(
        `/api/experiences/search?q=${encodeURIComponent(query)}&k=10`
      );
      setSearchResults(await res.json());
    } finally {
      setSearching(false);
    }
  };

  const filtered = (experiences ?? []).filter((exp) => {
    if (filter === "positive") return exp.valence > 0;
    if (filter === "negative") return exp.valence < 0;
    if (filter === "pending") return exp.status === "pending";
    return true;
  });

  const toggleSort = (col: "timestamp" | "valence") => {
    if (sortBy === col) {
      setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(col);
      setSortOrder("desc");
    }
  };

  const sorted = [...filtered].sort((a, b) => {
    const mul = sortOrder === "asc" ? 1 : -1;
    if (sortBy === "valence") return (a.valence - b.valence) * mul;
    return (new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()) * mul;
  });

  const displayList = searchResults
    ? [
        ...searchResults.best.map((r) => r.experience),
        ...searchResults.avoid.map((r) => r.experience),
      ]
    : sorted;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search experiences..."
          className="flex-1 bg-engram-card border border-engram-border rounded-lg px-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-engram-purple"
        />
        <button
          onClick={handleSearch}
          disabled={searching}
          className="px-4 py-2 bg-engram-purple/20 text-engram-purple rounded-lg text-sm hover:bg-engram-purple/30 transition-colors disabled:opacity-50"
        >
          {searching ? "..." : "Search"}
        </button>
      </div>

      <div className="flex gap-2">
        {(["all", "positive", "negative", "pending"] as const).map((f) => (
          <button
            key={f}
            onClick={() => {
              setFilter(f);
              setSearchResults(null);
            }}
            className={`px-3 py-1 rounded-lg text-xs capitalize ${
              filter === f
                ? "bg-engram-purple/20 text-engram-purple"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="rounded-xl bg-engram-card border border-engram-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-engram-border text-gray-500 text-xs uppercase">
              <th className="text-left p-3">Action</th>
              <th className="text-left p-3">Context</th>
              <th className="text-left p-3">Outcome</th>
              <th
                className="text-center p-3 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("valence")}
              >
                Valence {sortBy === "valence" ? (sortOrder === "asc" ? "↑" : "↓") : ""}
              </th>
              <th
                className="text-right p-3 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("timestamp")}
              >
                Time {sortBy === "timestamp" ? (sortOrder === "asc" ? "↑" : "↓") : ""}
              </th>
            </tr>
          </thead>
          <tbody>
            {displayList.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-gray-500">
                  No experiences found.
                </td>
              </tr>
            ) : (
              displayList.map((exp) => (
                <React.Fragment key={exp.id}>
                  <tr
                    onClick={() =>
                      setExpandedId(expandedId === exp.id ? null : exp.id)
                    }
                    className="border-b border-engram-border/50 hover:bg-engram-border/20 cursor-pointer"
                  >
                    <td className="p-3 text-gray-300 max-w-[200px] truncate">
                      {exp.action}
                    </td>
                    <td className="p-3 text-gray-400 max-w-[150px] truncate">
                      {exp.context}
                    </td>
                    <td className="p-3 text-gray-400 max-w-[200px] truncate">
                      {exp.outcome}
                    </td>
                    <td className="p-3 text-center">{valenceBadge(exp.valence)}</td>
                    <td className="p-3 text-right text-gray-500 text-xs">
                      {new Date(exp.timestamp).toLocaleString()}
                    </td>
                  </tr>
                  {expandedId === exp.id && (
                    <tr>
                      <td colSpan={5} className="p-4 bg-engram-bg/50 text-xs">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <strong className="text-gray-400">ID:</strong>{" "}
                            <span className="text-gray-500 font-mono">{exp.id}</span>
                          </div>
                          <div>
                            <strong className="text-gray-400">Status:</strong>{" "}
                            <span className="text-gray-500">{exp.status}</span>
                          </div>
                          <div className="col-span-2">
                            <strong className="text-gray-400">Action:</strong>{" "}
                            <span className="text-gray-300">{exp.action}</span>
                          </div>
                          <div className="col-span-2">
                            <strong className="text-gray-400">Context:</strong>{" "}
                            <span className="text-gray-300">{exp.context}</span>
                          </div>
                          <div className="col-span-2">
                            <strong className="text-gray-400">Outcome:</strong>{" "}
                            <span className="text-gray-300">{exp.outcome}</span>
                          </div>
                          <div className="col-span-2">
                            <strong className="text-gray-400">Metadata:</strong>{" "}
                            <span className="text-gray-500 font-mono">
                              {JSON.stringify(exp.metadata)}
                            </span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify page renders**

Run: `cd dashboard && npm run dev` — navigate to http://localhost:3000/experiences
Expected: Search bar, filter toggles, empty table with "No experiences found."

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/app/experiences/
git commit -m "feat(dashboard): add Experiences page with search, filters, and expandable table"
```

---

### Task 10: Skills Page

**Files:**
- Create: `dashboard/src/app/skills/page.tsx`

- [ ] **Step 1: Create Skills page**

Create `dashboard/src/app/skills/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Skill } from "@/lib/types";
import { motion } from "framer-motion";

export default function SkillsPage() {
  const {
    data: skills,
    setData: setSkills,
    refetch,
  } = useApi<Skill[]>("/api/skills");
  const [crystallizing, setCrystallizing] = useState(false);
  const [evolving, setEvolving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useWebSocket({
    "skill.crystallized": (data) => {
      setSkills((prev) =>
        prev ? [...prev, data as Skill] : [data as Skill]
      );
    },
  });

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const handleCrystallize = async () => {
    setCrystallizing(true);
    try {
      const res = await fetch("/api/crystallize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const result = await res.json();
      showToast(`Crystallized ${result.length} skill(s)`);
      refetch();
    } catch {
      showToast("Crystallize failed");
    } finally {
      setCrystallizing(false);
    }
  };

  const handleEvolve = async () => {
    setEvolving(true);
    try {
      const res = await fetch("/api/evolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const result = await res.json();
      showToast(result ? "Config evolved!" : "No unapplied skills");
      refetch();
    } catch {
      showToast("Evolve failed");
    } finally {
      setEvolving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <button
          onClick={handleCrystallize}
          disabled={crystallizing}
          className="px-4 py-2 bg-engram-green/20 text-engram-green rounded-lg text-sm hover:bg-engram-green/30 transition-colors disabled:opacity-50"
        >
          {crystallizing ? "Crystallizing..." : "Crystallize Now"}
        </button>
        <button
          onClick={handleEvolve}
          disabled={evolving}
          className="px-4 py-2 bg-engram-amber/20 text-engram-amber rounded-lg text-sm hover:bg-engram-amber/30 transition-colors disabled:opacity-50"
        >
          {evolving ? "Evolving..." : "Evolve Config"}
        </button>
      </div>

      {toast && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-engram-card border border-engram-border rounded-lg px-4 py-2 text-sm text-gray-300"
        >
          {toast}
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(skills ?? []).length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            No skills crystallized yet.
          </div>
        ) : (
          (skills ?? []).map((skill, i) => (
            <motion.div
              key={skill.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-xl bg-engram-card border border-engram-border p-4 space-y-3"
            >
              <div>
                <h3 className="text-sm font-medium text-gray-200">
                  {skill.rule}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  {skill.context_pattern}
                </p>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">Confidence</span>
                  <span className="text-gray-400 font-mono">
                    {(skill.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-1.5 bg-engram-border rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${skill.confidence * 100}%`,
                      background:
                        skill.confidence >= 0.8
                          ? "#34d399"
                          : skill.confidence >= 0.5
                            ? "#fbbf24"
                            : "#f87171",
                    }}
                  />
                </div>
              </div>

              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-0.5 bg-engram-purple/10 text-engram-purple rounded text-xs">
                  {skill.evidence_count} evidence
                </span>
                <span className="px-2 py-0.5 bg-engram-green/10 text-engram-green rounded text-xs">
                  +{skill.valence_summary.positive}
                </span>
                <span className="px-2 py-0.5 bg-engram-red/10 text-engram-red rounded text-xs">
                  -{skill.valence_summary.negative}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    skill.applied
                      ? "bg-engram-green/10 text-engram-green"
                      : "bg-engram-amber/10 text-engram-amber"
                  }`}
                >
                  {skill.applied ? "Applied" : "Unapplied"}
                </span>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify page renders**

Run: `cd dashboard && npm run dev` — navigate to http://localhost:3000/skills
Expected: Action buttons visible, "No skills crystallized yet." message.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/app/skills/
git commit -m "feat(dashboard): add Skills page with card grid and crystallize/evolve actions"
```

---

### Task 11: Graph Page

**Files:**
- Create: `dashboard/src/app/graph/page.tsx`

- [ ] **Step 1: Create Graph page**

Create `dashboard/src/app/graph/page.tsx`:

```tsx
"use client";

import dynamic from "next/dynamic";
import { useApi } from "@/hooks/useApi";
import { GraphData } from "@/lib/types";
import { useCallback, useRef, useState } from "react";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

function drawHexagon(ctx: CanvasRenderingContext2D, x: number, y: number, r: number) {
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    const px = x + r * Math.cos(angle);
    const py = y + r * Math.sin(angle);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

export default function GraphPage() {
  const { data: graph, loading } = useApi<GraphData>("/api/graph");
  const fgRef = useRef<any>(null);
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());

  const graphData =
    graph && graph.nodes.length > 0
      ? {
          nodes: graph.nodes.map((n) => ({ ...n })),
          links: graph.edges.map((e) => ({
            source: e.source,
            target: e.target,
            type: e.type,
            weight: e.weight,
          })),
        }
      : { nodes: [], links: [] };

  const nodeLabel = useCallback((node: any) => {
    if (node.type === "skill")
      return `Skill: ${node.label}\nConfidence: ${((node.confidence ?? 0) * 100).toFixed(0)}%`;
    return `${node.label}\nValence: ${(node.valence ?? 0).toFixed(2)}`;
  }, []);

  const linkColor = useCallback(
    (link: any) => {
      const srcId = typeof link.source === "object" ? link.source.id : link.source;
      const tgtId = typeof link.target === "object" ? link.target.id : link.target;
      if (highlightNodes.size > 0 && (highlightNodes.has(srcId) || highlightNodes.has(tgtId))) {
        return link.type === "source" ? "rgba(129,140,248,0.7)" : "rgba(148,163,184,0.5)";
      }
      return link.type === "source"
        ? "rgba(129,140,248,0.3)"
        : "rgba(148,163,184,0.15)";
    },
    [highlightNodes]
  );

  const handleNodeClick = useCallback(
    (node: any) => {
      const connectedIds = new Set<string>();
      connectedIds.add(node.id);
      graphData.links.forEach((link: any) => {
        const srcId = typeof link.source === "object" ? link.source.id : link.source;
        const tgtId = typeof link.target === "object" ? link.target.id : link.target;
        if (srcId === node.id) connectedIds.add(tgtId);
        if (tgtId === node.id) connectedIds.add(srcId);
      });
      setHighlightNodes((prev) =>
        prev.has(node.id) ? new Set() : connectedIds
      );
    },
    [graphData.links]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-120px)] text-gray-500">
        Loading graph...
      </div>
    );
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-120px)] text-gray-500">
        No data to visualize.
      </div>
    );
  }

  return (
    <div
      className="rounded-xl bg-engram-card border border-engram-border overflow-hidden"
      style={{ height: "calc(100vh - 120px)" }}
    >
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel={nodeLabel}
        linkColor={linkColor}
        linkWidth={(link: any) => (link.type === "source" ? 1.5 : 0.5)}
        backgroundColor="#0f0f23"
        onNodeClick={handleNodeClick}
        onBackgroundClick={() => setHighlightNodes(new Set())}
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const isHighlighted = highlightNodes.size === 0 || highlightNodes.has(node.id);
          const alpha = isHighlighted ? 0.9 : 0.2;

          if (node.type === "skill") {
            const r = 4 + (node.confidence ?? 0.5) * 4;
            drawHexagon(ctx, node.x!, node.y!, r);
            ctx.fillStyle = `rgba(251,191,36,${alpha})`;
            ctx.fill();
            ctx.strokeStyle = `rgba(251,191,36,${Math.min(alpha + 0.2, 1)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          } else {
            const r = 2 + Math.abs(node.valence ?? 0) * 4;
            ctx.beginPath();
            ctx.arc(node.x!, node.y!, r, 0, 2 * Math.PI);
            const color = (node.valence ?? 0) >= 0 ? "52,211,153" : "248,113,113";
            ctx.fillStyle = `rgba(${color},${alpha})`;
            ctx.fill();
          }
        }}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const r = node.type === "skill" ? 8 : 6;
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, r, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        warmupTicks={50}
        cooldownTicks={100}
      />
    </div>
  );
}
```

- [ ] **Step 2: Verify page renders**

Run: `cd dashboard && npm run dev` — navigate to http://localhost:3000/graph
Expected: Shows "No data to visualize." (empty state)

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/app/graph/
git commit -m "feat(dashboard): add Graph page with force-directed neural visualization"
```

---

### Task 12: Build Pipeline + Static File Integration

**Files:**
- Modify: `pyproject.toml` (include static files in wheel)

- [ ] **Step 1: Add static files to pyproject.toml package data**

In `pyproject.toml`, ensure the dashboard static directory is included. Since hatchling is the build backend, add under `[tool.hatch.build.targets.wheel]`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/engram_ai"]

[tool.hatch.build.targets.wheel.force-include]
"src/engram_ai/dashboard/static" = "engram_ai/dashboard/static"
```

- [ ] **Step 2: Build the frontend**

Run:
```bash
cd dashboard && npm run build
```
Expected: Next.js generates `dashboard/out/` directory with static HTML/JS/CSS files.

- [ ] **Step 3: Copy built files to static directory**

Run:
```bash
cp -r dashboard/out/. src/engram_ai/dashboard/static/
```
Expected: `src/engram_ai/dashboard/static/` now contains `index.html` and other files.

Note: Using `out/.` instead of `out/*` ensures hidden files are copied (works in Git Bash on Windows).

- [ ] **Step 5: Remove .gitkeep (no longer needed) and verify static files**

Run: `rm src/engram_ai/dashboard/static/.gitkeep`
Run: `ls src/engram_ai/dashboard/static/`
Expected: `index.html`, `experiences/`, `skills/`, `graph/`, `_next/` directories

- [ ] **Step 6: Run all backend tests to verify nothing broke**

Run: `python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 7: Verify end-to-end: launch dashboard and check browser**

Run: `python -m engram_ai.cli dashboard --port 3333`
Expected: Dashboard serves at http://localhost:3333 — pages load, navigation works.

- [ ] **Step 8: Commit all static files + config changes**

```bash
git add .gitignore pyproject.toml src/engram_ai/dashboard/static/
git commit -m "feat(dashboard): build frontend and integrate static files for serving"
```

---

### Task 13: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests pass (existing + dashboard)

- [ ] **Step 2: Run ruff linter**

Run: `ruff check src/engram_ai/dashboard/`
Expected: No lint errors

- [ ] **Step 3: Verify dashboard serves correctly**

Run: `python -m engram_ai.cli dashboard --port 3333`
Verify in browser:
- http://localhost:3333 — Overview page loads with stats cards, chart, graph, recent list
- http://localhost:3333/experiences — Table with search and filters
- http://localhost:3333/skills — Card grid with action buttons
- http://localhost:3333/graph — Force-directed graph (or empty state)
- Navigation tabs work between all pages

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add src/engram_ai/dashboard/ tests/dashboard/
git commit -m "fix(dashboard): final adjustments from integration testing"
```
