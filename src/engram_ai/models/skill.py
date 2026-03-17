# src/engram_ai/models/skill.py
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field

class Skill(BaseModel):
    """A crystallized skill extracted from experience patterns."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 2
    rule: str
    context_pattern: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_experiences: list[str]
    evidence_count: int
    valence_summary: dict
    created_at: datetime = Field(default_factory=datetime.now)

    # v0.2: Reinforcement & Decay
    last_reinforced_at: datetime | None = None
    reinforcement_count: int = 0

    # v0.2: Anti-Skill
    skill_type: str = "positive"  # "positive" | "anti"

    # v0.2: Conflict Detection
    conflicts_with: list[str] = Field(default_factory=list)

    # v0.2: Lifecycle status
    status: str = "active"  # "active" | "superseded"
