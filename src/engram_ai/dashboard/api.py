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


def get_forge(request: Request) -> "Forge":
    project = request.query_params.get("project")
    return request.app.state.project_manager.get_forge(project)


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
