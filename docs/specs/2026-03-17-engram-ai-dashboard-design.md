# Engram-AI Web Dashboard Design Spec

## Goal

Provide a real-time web dashboard for visualizing experiences, skills, and the neural graph of Engram-AI. Serves three use cases: personal monitoring, team sharing, and demo/showcase for attracting GitHub stars.

## Architecture

```
User
  │
  ▼
engram-ai dashboard  (CLI command, --port 3333)
  │
  ▼
FastAPI Server (Python, uvicorn)
  ├── REST API (/api/*)
  ├── WebSocket (/ws) — EventBus → real-time push via asyncio.Queue
  └── Static Files (html=True) — pre-built Next.js SPA
        │
        ▼
  Next.js SPA (React 18, static export)
  ├── Overview page
  ├── Experiences page
  ├── Skills page
  └── Graph page
```

### Key Decisions

- **No Node.js required for users** — Next.js is statically exported at build time; built HTML/JS/CSS is committed to git and served by FastAPI's `StaticFiles`.
- **Developers** who want to modify the frontend run `cd dashboard && npm run dev`.
- **FastAPI reuses the existing Forge facade** — no new storage or business logic (except one new `/api/graph` endpoint).
- **WebSocket bridges EventBus to browser** — uses `asyncio.Queue` per connection to bridge sync EventBus callbacks to async WebSocket sends.
- **Forge singleton** — `create_app()` reads config via `_load_config()` (same as CLI) and stores Forge on `app.state.forge`. All endpoints access it via FastAPI dependency injection.

## Backend: FastAPI

### Files

- `src/engram_ai/dashboard/__init__.py`
- `src/engram_ai/dashboard/api.py` — REST + WebSocket endpoints
- `src/engram_ai/dashboard/server.py` — FastAPI app factory, static file mount, Forge singleton

### REST Endpoints

| Method | Path | Maps to | Response |
|--------|------|---------|----------|
| GET | `/api/status` | `forge.status()` | `{"total_experiences": int, "total_skills": int, "unapplied_skills": int}` |
| GET | `/api/experiences` | `storage.get_all_experiences()` | `[Experience.model_dump(), ...]` |
| GET | `/api/experiences/search?q=...&k=5` | `forge.query(q, k)` | `{"best": [{"experience": {...}, "score": float}, ...], "avoid": [{"experience": {...}, "score": float}, ...]}` |
| GET | `/api/skills` | `storage.get_all_skills()` + applied status | `[{...Skill.model_dump(), "applied": bool}, ...]` |
| GET | `/api/graph` | server-side graph computation | `{"nodes": [...], "edges": [...]}` (see Graph section) |
| POST | `/api/crystallize` | `forge.crystallize(body)` | `[Skill.model_dump(), ...]` |
| POST | `/api/evolve` | `forge.evolve(body)` | `EvolutionRecord.model_dump() \| null` |

All endpoints return JSON. CORS enabled for development (localhost origins).

### Request Body Schemas

```python
class CrystallizeRequest(BaseModel):
    min_experiences: int = 3
    min_confidence: float = 0.7

class EvolveRequest(BaseModel):
    config_path: str = "./CLAUDE.md"
```

### Skills Applied Status

The `Skill` Pydantic model has no `applied` field — applied state is tracked in ChromaDB metadata only. The `/api/skills` endpoint resolves this by:
1. Calling `storage.get_all_skills()` for all skills
2. Calling `storage.get_unapplied_skills()` for unapplied IDs
3. Merging: adding `"applied": True/False` to each skill's JSON based on whether its ID appears in the unapplied list

### Graph Endpoint `/api/graph`

Computes the full graph server-side in a single pass:

```python
GET /api/graph

Response:
{
  "nodes": [
    {"id": "exp-xxx", "type": "experience", "label": "action text", "valence": 0.8, "timestamp": "..."},
    {"id": "skill-xxx", "type": "skill", "label": "rule text", "confidence": 0.85}
  ],
  "edges": [
    {"source": "exp-xxx", "target": "skill-xxx", "type": "source"},
    {"source": "exp-aaa", "target": "exp-bbb", "type": "similarity", "weight": 0.45}
  ]
}
```

Algorithm:
1. Load all experiences and skills
2. For each skill, create edges from `skill.source_experiences` → skill
3. For each experience, query top-5 similar experiences; add edges where similarity > 0.3 and not self
4. Deduplicate bidirectional similarity edges (keep highest weight)

### WebSocket `/ws`

**Sync-to-async bridge:** Since EventBus is synchronous and FastAPI WebSockets are async, each connection uses an `asyncio.Queue`:

```python
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    def on_event(event_name: str):
        def handler(payload):
            data = {"event": event_name, "data": payload.model_dump()}
            queue.put_nowait(data)  # sync-safe: put_nowait from sync callback
        return handler

    handlers = {}
    for event in [EXPERIENCE_RECORDED, EXPERIENCE_PENDING, SKILL_CRYSTALLIZED, AGENT_EVOLVED]:
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

Events pushed:
- `experience.recorded` → `{"event": "experience.recorded", "data": Experience.model_dump()}`
- `experience.pending` → `{"event": "experience.pending", "data": Experience.model_dump()}`
- `skill.crystallized` → `{"event": "skill.crystallized", "data": Skill.model_dump()}`
- `agent.evolved` → `{"event": "agent.evolved", "data": EvolutionRecord.model_dump()}`

**Note:** `queue.put_nowait()` is safe to call from a synchronous context because it doesn't await. The async `queue.get()` blocks the WebSocket send loop until data arrives.

### Forge Singleton in FastAPI

```python
def create_app() -> FastAPI:
    app = FastAPI(title="Engram-AI Dashboard")

    # Reuse CLI config resolution
    storage_override = os.environ.get("ENGRAM_AI_STORAGE")
    if storage_override:
        forge = Forge(storage_path=storage_override)
    elif CONFIG_FILE.exists():
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        forge = Forge(storage_path=config.get("storage_path", str(CONFIG_DIR / "data")))
    else:
        forge = Forge()

    app.state.forge = forge

    # Mount API routes
    app.include_router(api_router)

    # Mount static files LAST (catch-all for SPA routing)
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
```

`StaticFiles(html=True)` enables HTML fallback — navigating to `/experiences` serves `experiences/index.html`, enabling SPA client-side routing.

### CLI Command

Add to `src/engram_ai/cli.py`:

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

## Frontend: Next.js SPA

### Directory Structure

```
dashboard/
├── package.json
├── next.config.mjs         # output: 'export'
├── tailwind.config.ts
├── postcss.config.mjs
├── tsconfig.json
├── src/
│   ├── app/
│   │   ├── layout.tsx      # Root layout: dark theme, nav tabs
│   │   ├── page.tsx        # Overview page
│   │   ├── experiences/
│   │   │   └── page.tsx    # Experiences table
│   │   ├── skills/
│   │   │   └── page.tsx    # Skills cards
│   │   └── graph/
│   │       └── page.tsx    # Neural graph
│   ├── components/
│   │   ├── StatsCards.tsx
│   │   ├── ValenceTrend.tsx
│   │   ├── RecentExperiences.tsx
│   │   ├── MiniGraph.tsx
│   │   ├── ExperienceTable.tsx
│   │   ├── SkillCard.tsx
│   │   ├── NeuralGraph.tsx
│   │   └── NavTabs.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   └── useApi.ts
│   └── lib/
│       └── types.ts        # Experience, Skill, Status TypeScript types
└── public/
```

### Pages

#### Overview (`/`)

Layout (top to bottom):
1. **Stats Cards row** — 3 cards: Experiences (purple), Skills (green), Unapplied Skills (amber). Large numbers with subtle glow. Data from `/api/status`.
2. **Middle row** (2 columns):
   - Left: **Valence Trend** — Area chart (Recharts) showing valence over time. Green fill for positive, red for negative. Data from `/api/experiences` sorted by timestamp.
   - Right: **Mini Neural Graph** — Animated force-directed graph preview. Nodes pulse with `framer-motion`. Click to go to full Graph page. Data from `/api/graph`.
3. **Recent Experiences** — Last 10 experiences with valence color coding. Real-time updates via WebSocket.

#### Experiences (`/experiences`)

- **Search bar** at top — calls `/api/experiences/search?q=...`
- **Filter toggles** — All / Positive / Negative / Pending
- **Data table** — columns: Action, Context, Outcome, Valence (colored badge), Timestamp
- Sortable by valence or timestamp
- Clicking a row expands to show full metadata

#### Skills (`/skills`)

- **Card grid** — Each skill as a card:
  - Rule text (title)
  - Context pattern (subtitle)
  - Confidence bar (horizontal, colored by confidence level)
  - Evidence count badge
  - Valence summary (positive/negative bar)
  - Applied/Unapplied status badge (from `/api/skills` merged `applied` field)
- **Action buttons** at top:
  - "Crystallize Now" → POST `/api/crystallize`
  - "Evolve Config" → POST `/api/evolve`
- Buttons show loading state and result toast notification

#### Graph (`/graph`)

- **Full-screen force-directed graph** using `react-force-graph-2d`
- Data from `GET /api/graph` (pre-computed server-side)
- **Nodes:**
  - Experience nodes — circles, colored by valence (green gradient for positive, red for negative, size by abs(valence))
  - Skill nodes — hexagons/diamonds, colored gold, size by confidence
- **Edges:**
  - Experience → Skill links (type: "source")
  - Experience → Experience similarity links (type: "similarity", weight > 0.3)
- **Interactions:** Zoom, pan, hover tooltip (shows experience/skill details), click to highlight connected nodes
- **Animated:** Nodes gently drift, new nodes appear with fade-in animation

### Design System

- **Theme:** Dark background (`#0f0f23`), card background (`#1a1a3e`)
- **Colors:**
  - Purple (`#818cf8` / `#a78bfa`) — primary, experiences
  - Green (`#34d399` / `#6ee7b7`) — positive, skills
  - Red (`#f87171` / `#fca5a5`) — negative, avoid
  - Amber (`#fbbf24` / `#fcd34d`) — evolution, neutral
- **Typography:** Inter font, monospace for data values
- **Animations:** framer-motion for page transitions, stats counter animation, node pulsing

### Real-time Updates

`useWebSocket` hook:
```typescript
// Connects to ws://host:port/ws
// On message: dispatch to relevant React state
// Auto-reconnect on disconnect (exponential backoff, max 5 retries)
```

All pages subscribe to WebSocket events and update their state accordingly:
- `experience.recorded` → Overview updates stats + recent list, Experiences adds row, Graph adds node
- `skill.crystallized` → Overview updates stats, Skills adds card, Graph adds node
- `agent.evolved` → Overview updates stats, toast notification

## Dependencies

### Python (add to pyproject.toml)

```toml
dependencies = [
    # ... existing ...
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
]
```

Note: `uvicorn[standard]` includes `websockets` transitively.

### Frontend (dashboard/package.json)

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "recharts": "^2.12.0",
    "react-force-graph-2d": "^1.25.0",
    "framer-motion": "^11.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.3.0",
    "@types/node": "^22.0.0"
  }
}
```

Version rationale: React 18 + Next.js 14 + framer-motion 11 + Tailwind 3 are a proven, stable combination with no peer dependency conflicts.

## Packaging

1. Frontend is built with `cd dashboard && npm run build` → outputs to `dashboard/out/`
2. Built files are copied to `src/engram_ai/dashboard/static/`
3. Static files are committed to git (users don't need Node.js)
4. FastAPI mounts `StaticFiles(directory=..., html=True)` at `/` — `html=True` enables SPA route fallback (e.g., `/experiences` serves `experiences/index.html`)
5. `pyproject.toml` includes `src/engram_ai/dashboard/static/**` in wheel

## Testing

### Backend Tests (`tests/dashboard/`)

- `test_api.py` — Test all REST endpoints with httpx.AsyncClient and Forge with MockLLM
  - GET /api/status returns correct counts
  - GET /api/experiences returns all stored experiences
  - GET /api/experiences/search returns best/avoid with scores
  - GET /api/skills returns all skills with applied status
  - GET /api/graph returns nodes and edges
  - POST /api/crystallize triggers crystallization
  - POST /api/evolve triggers evolution
- `test_websocket.py` — Test WebSocket event delivery
  - Connect, record experience, verify event received as JSON
  - Connect, crystallize, verify skill event received
  - Disconnect cleanup (no lingering EventBus subscribers)

### Frontend

- Static build verification (files exist, index.html valid)
- No frontend unit tests in v0.1 (deferred — manual browser testing sufficient)

## Error Handling

- All API endpoints return JSON error responses: `{"detail": "error message"}`
- WebSocket errors are logged server-side, connection stays open
- Frontend shows toast notifications for errors from API calls
- Dashboard gracefully shows "No data" states when storage is empty

## Out of Scope (v0.1)

- Authentication / authorization
- Multi-user / multi-tenant
- Persistent dashboard settings
- Light theme (dark only for now)
- Frontend unit tests
- Server-side rendering (static export only)
