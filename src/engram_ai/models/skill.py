# src/engram_ai/models/skill.py
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field

class Skill(BaseModel):
    """A crystallized skill extracted from experience patterns."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 1
    rule: str
    context_pattern: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_experiences: list[str]
    evidence_count: int
    valence_summary: dict
    created_at: datetime = Field(default_factory=datetime.now)
