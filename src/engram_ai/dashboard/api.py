"""REST API and WebSocket endpoints for Engram-AI dashboard."""

from __future__ import annotations

import asyncio
from typing import Any

try:
    from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
    from pydantic import BaseModel
    from starlette.requests import Request
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from engram_ai.events.events import (
    AGENT_EVOLVED,
    EXPERIENCE_PENDING,
    EXPERIENCE_RECORDED,
    SKILL_CRYSTALLIZED,
)
from engram_ai.forge import Forge


def get_forge(request: "Request") -> "Forge":
    project = request.query_params.get("project")
    return request.app.state.project_manager.get_forge(project)


# --- Request schemas ---


if _FASTAPI_AVAILABLE:
    class CrystallizeRequest(BaseModel):
        min_experiences: int = 3
        min_confidence: float = 0.7

    class EvolveRequest(BaseModel):
        config_path: str = "./CLAUDE.md"


def create_router(project_manager):
    """Factory function that creates and returns the API router."""
    if not _FASTAPI_AVAILABLE:
        raise ImportError(
            "fastapi package is required for the dashboard. "
            "Install it with: pip install engram-ai[dashboard]"
        )

    router = APIRouter(prefix="/api")

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
        experiences = forge._storage.get_all_experiences()
        all_skills = forge._storage.get_all_skills_including_superseded()

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        exp_ids = set()
        skill_ids = set()

        for exp in experiences:
            exp_ids.add(exp.id)
            nodes.append({
                "id": exp.id, "type": "experience",
                "label": exp.action[:80],
                "valence": exp.valence,
                "timestamp": exp.timestamp.isoformat(),
                "parent_id": exp.parent_id,
                "related_ids": exp.related_ids,
            })

        for skill in all_skills:
            skill_ids.add(skill.id)
            nodes.append({
                "id": skill.id, "type": "skill",
                "label": skill.rule[:80],
                "confidence": skill.confidence,
                "skill_type": skill.skill_type,
                "status": skill.status,
                "conflicts_with": skill.conflicts_with,
            })
            for src_id in skill.source_experiences:
                if src_id in exp_ids:
                    edges.append({"source": src_id, "target": skill.id, "type": "source"})

        # Chain edges
        for exp in experiences:
            if exp.parent_id and exp.parent_id in exp_ids:
                edges.append({"source": exp.parent_id, "target": exp.id, "type": "chain"})

        # Related edges
        for exp in experiences:
            for related_id in exp.related_ids:
                if related_id in exp_ids and related_id != exp.id:
                    edges.append({"source": exp.id, "target": related_id, "type": "related"})

        # Conflict edges (deduplicate)
        seen_conflicts: set[tuple[str, str]] = set()
        for skill in all_skills:
            for conflict_id in skill.conflicts_with:
                pair = tuple(sorted([skill.id, conflict_id]))
                if pair not in seen_conflicts and conflict_id in skill_ids:
                    seen_conflicts.add(pair)
                    edges.append({"source": skill.id, "target": conflict_id, "type": "conflict"})

        # Similarity edges
        seen_sim_pairs: set[tuple[str, str]] = set()
        for exp in experiences:
            similar = forge._storage.query_experiences(exp.context, k=3)
            for sim_exp, score in similar:
                if sim_exp.id != exp.id and score > 0.5:
                    pair = tuple(sorted([exp.id, sim_exp.id]))
                    if pair not in seen_sim_pairs:
                        seen_sim_pairs.add(pair)
                        edges.append({
                            "source": exp.id, "target": sim_exp.id,
                            "type": "similarity", "weight": round(score, 2),
                        })

        return {"nodes": nodes, "edges": edges}

    @router.get("/projects")
    async def list_projects(request: Request) -> list[str]:
        return request.app.state.project_manager.list_projects()

    @router.get("/scheduler/status")
    async def scheduler_status(request: Request) -> dict:
        scheduler = getattr(request.app.state, "scheduler", None)
        if scheduler is None:
            return {"enabled": False, "running": False}
        return scheduler.get_status()

    @router.post("/scheduler/toggle")
    async def scheduler_toggle(request: Request) -> dict:
        scheduler = getattr(request.app.state, "scheduler", None)
        if scheduler is None:
            return {"enabled": False, "running": False}
        if scheduler.is_running:
            await scheduler.stop()
        else:
            await scheduler.start()
        return scheduler.get_status()

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

    return router


def create_ws_router(project_manager):
    """Factory function that creates and returns the WebSocket router."""
    if not _FASTAPI_AVAILABLE:
        raise ImportError(
            "fastapi package is required for the dashboard. "
            "Install it with: pip install engram-ai[dashboard]"
        )

    ws_router = APIRouter()

    @ws_router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        project = websocket.query_params.get("project")
        forge: Forge = websocket.app.state.project_manager.get_forge(project)
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def on_event(event_name: str):
            def handler(payload):
                data = {"event": event_name, "data": payload.model_dump(mode="json")}
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

    return ws_router
