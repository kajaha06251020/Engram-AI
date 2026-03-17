"""FastAPI application factory for Engram-AI dashboard."""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from engram_ai.dashboard.api import router, ws_router
from engram_ai.project import ProjectManager
from engram_ai.scheduler import Scheduler, SchedulerConfig

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".engram-ai"
CONFIG_FILE = CONFIG_DIR / "config.json"


def create_app(
    project_manager: ProjectManager | None = None,
    scheduler_config: SchedulerConfig | None = None,
) -> FastAPI:
    """Create and configure the dashboard FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        pm = app.state.project_manager
        config = scheduler_config or SchedulerConfig(
            **app.state.raw_config.get("scheduler", {})
        )
        scheduler = Scheduler(pm, config)
        app.state.scheduler = scheduler
        await scheduler.start()
        yield
        await scheduler.stop()

    app = FastAPI(title="Engram-AI Dashboard", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3333"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if project_manager:
        app.state.project_manager = project_manager
        app.state.raw_config = {}
    else:
        config = {}
        if CONFIG_FILE.exists():
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        base_path = Path(
            os.environ.get(
                "ENGRAM_AI_STORAGE",
                config.get("storage_path", str(CONFIG_DIR / "data")),
            )
        )
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        llm = None
        if api_key:
            from engram_ai.llm.claude import ClaudeLLM
            llm = ClaudeLLM(api_key=api_key)
        app.state.project_manager = ProjectManager(
            base_path=base_path, llm=llm, config=config
        )
        app.state.raw_config = config

    app.include_router(router)
    app.include_router(ws_router)

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists() and any(static_dir.iterdir()):
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
