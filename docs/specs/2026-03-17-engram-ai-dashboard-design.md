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
  ├── WebSocket (/ws) — EventBus → real-time push
  └── Static Files — pre-built Next.js SPA
        │
        ▼
  Next.js SPA (React, static export)
  ├── Overview page
  ├── Experiences page
  ├── Skills page
  └── Graph page
```

### Key Decisions

- **No Node.js required for users** — Next.js is statically exported at build time; built HTML/JS/CSS is committed to git and served by FastAPI's `StaticFiles`.
- **Developers** who want to modify the frontend run `cd dashboard && npm run dev`.
- **FastAPI reuses the existing Forge facade** — no new storage or business logic.
- **WebSocket bridges EventBus to browser** — the FastAPI server subscribes to EventBus events and pushes them as JSON over WebSocket.

## Backend: FastAPI

### Files

- `src/engram_ai/dashboard/__init__.py`
- `src/engram_ai/dashboard/api.py` — REST + WebSocket endpoints
- `src/engram_ai/dashboard/server.py` — FastAPI app factory, static file mount, CLI integration

### REST Endpoints

| Method | Path | Maps to | Response |
|--------|------|---------|----------|
| GET | `/api/status` | `forge.status()` | `{"total_experiences": int, "total_skills": int, "unapplied_skills": int}` |
| GET | `/api/experiences` | `storage.get_all_experiences()` | `[Experience.model_dump(), ...]` |
| GET | `/api/experiences/search?q=...&k=5` | `forge.query(q, k)` | `{"best": [...], "avoid": [...]}` |
| GET | `/api/skills` | `storage.get_all_skills()` | `[Skill.model_dump(), ...]` |
| POST | `/api/crystallize` | `forge.crystallize(body.min_experiences, body.min_confidence)` | `[Skill.model_dump(), ...]` |
| POST | `/api/evolve` | `forge.evolve(body.config_path)` | `EvolutionRecord.model_dump() | null` |

All endpoints return JSON. CORS enabled for development (localhost origins).

### WebSocket `/ws`

On connect, the server subscribes to all EventBus events for this connection:
- `experience.recorded` → `{"event": "experience.recorded", "data": Experience.model_dump()}`
- `experience.pending` → `{"event": "experience.pending", "data": Experience.model_dump()}`
- `skill.crystallized` → `{"event": "skill.crystallized", "data": Skill.model_dump()}`
- `agent.evolved` → `{"event": "agent.evolved", "data": EvolutionRecord.model_dump()}`

On disconnect, unsubscribe all callbacks.

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
├── next.config.js          # output: 'export', basePath: ''
├── tailwind.config.js
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
1. **Stats Cards row** — 3 cards: Experiences (purple), Skills (green), Evolutions (amber). Large numbers with subtle glow.
2. **Middle row** (2 columns):
   - Left: **Valence Trend** — Area chart (Recharts) showing valence over time. Green fill for positive, red for negative.
   - Right: **Mini Neural Graph** — Animated force-directed graph preview. Nodes pulse with `framer-motion`. Click to go to full Graph page.
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
  - Valence summary (positive/negative pie or bar)
  - Applied/Unapplied status badge
- **Action buttons** at top:
  - "Crystallize Now" → POST `/api/crystallize`
  - "Evolve Config" → POST `/api/evolve`
- Buttons show loading state and result toast notification

#### Graph (`/graph`)

- **Full-screen force-directed graph** using `react-force-graph-2d`
- **Nodes:**
  - Experience nodes — circles, colored by valence (green gradient for positive, red for negative, size by abs(valence))
  - Skill nodes — hexagons/diamonds, colored gold, size by confidence
- **Edges:**
  - Experience → Skill links (from `skill.source_experiences`)
  - Experience → Experience similarity links (from query similarity, threshold > 0.3)
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
// Auto-reconnect on disconnect (exponential backoff)
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
    "websockets>=12.0",
]
```

### Frontend (dashboard/package.json)

```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "recharts": "^2.12.0",
    "react-force-graph-2d": "^1.25.0",
    "framer-motion": "^11.0.0",
    "tailwindcss": "^4.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^19.0.0",
    "@types/node": "^22.0.0"
  }
}
```

## Packaging

1. Frontend is built with `cd dashboard && npm run build` → outputs to `dashboard/out/`
2. Built files are copied to `src/engram_ai/dashboard/static/`
3. Static files are committed to git (users don't need Node.js)
4. FastAPI mounts `StaticFiles` at `/` pointing to the static directory
5. `pyproject.toml` includes `src/engram_ai/dashboard/static/**` in wheel

## Testing

### Backend Tests (`tests/dashboard/`)

- `test_api.py` — Test all REST endpoints with httpx.AsyncClient and Forge with MockLLM
  - GET /api/status returns correct counts
  - GET /api/experiences returns all stored experiences
  - GET /api/experiences/search returns best/avoid partitioned
  - GET /api/skills returns all skills
  - POST /api/crystallize triggers crystallization
  - POST /api/evolve triggers evolution
- `test_websocket.py` — Test WebSocket event delivery
  - Connect, record experience, verify event received
  - Connect, crystallize, verify skill event received
  - Disconnect cleanup (no lingering subscribers)

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
