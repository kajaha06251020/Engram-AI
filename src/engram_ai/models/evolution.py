# src/engram_ai/models/evolution.py
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field

class EvolutionRecord(BaseModel):
    """Record of an agent evolution event."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 1
    timestamp: datetime = Field(default_factory=datetime.now)
    skills_applied: list[str]
    config_path: str
    diff: str
