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
