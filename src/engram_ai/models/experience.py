# src/engram_ai/models/experience.py
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field

class Experience(BaseModel):
    """A recorded experience: action taken in a context, and its outcome."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 2
    action: str
    context: str
    outcome: str
    valence: float = Field(ge=-1.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
    status: str = "complete"

    # v0.2: Experience Chain
    parent_id: str | None = None
    related_ids: list[str] = Field(default_factory=list)
