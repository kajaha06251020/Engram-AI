import logging
import re
import sys
from pathlib import Path
from typing import Any

from engram_ai.events.bus import EventBus
from engram_ai.events.events import EXPERIENCE_CHAINED, EXPERIENCE_PENDING, EXPERIENCE_RECORDED
from engram_ai.models.experience import Experience
from engram_ai.storage.base import BaseStorage

logger = logging.getLogger(__name__)

POSITIVE_KEYWORDS = re.compile(
    r"完璧|perfect|great|thanks|良い|good|awesome|excellent|nice|素晴らしい|ありがとう|👍|LGTM",
    re.IGNORECASE,
)
NEGATIVE_KEYWORDS = re.compile(
    r"違う|wrong|fix|\bno[,.]\s|ダメ|だめ|間違|error|incorrect|やり直|修正して",
    re.IGNORECASE,
)
NEUTRAL_KEYWORDS = re.compile(
    r"^(ok|okay|まあ|fine|sure)[\s.,!]*$",
    re.IGNORECASE,
)


class Recorder:
    """Records experiences with two-phase pending support."""

    def __init__(self, storage: BaseStorage, event_bus: EventBus, pending_path: str = "", llm: Any = None) -> None:
        self._storage = storage
        self._event_bus = event_bus
        self._pending_path = Path(pending_path) if pending_path else None
        self._llm = llm

    def record(self, action: str, context: str, outcome: str, valence: float,
               metadata: dict | None = None, parent_id: str | None = None) -> Experience:
        # Auto-link: find related experiences
        related_ids = []
        try:
            similar = self._storage.query_experiences(context, k=5)
            related_ids = [exp.id for exp, sim in similar if sim >= 0.5][:5]
        except Exception:
            logger.warning("Auto-link failed, continuing without related_ids")

        exp = Experience(
            action=action, context=context, outcome=outcome,
            valence=valence, metadata=metadata or {},
            status="complete", parent_id=parent_id, related_ids=related_ids,
        )
        self._storage.store_experience(exp)
        self._event_bus.emit(EXPERIENCE_RECORDED, exp)
        if parent_id or related_ids:
            self._event_bus.emit(EXPERIENCE_CHAINED, exp)
        return exp

    def record_pending(self, action: str, context: str, metadata: dict | None = None,
                       parent_id: str | None = None) -> None:
        exp = Experience(action=action, context=context, outcome="", valence=0.0, metadata=metadata or {}, status="pending", parent_id=parent_id)
        if self._pending_path:
            self._pending_path.parent.mkdir(parents=True, exist_ok=True)
            self._locked_append(exp.model_dump_json() + "\n")
        self._event_bus.emit(EXPERIENCE_PENDING, exp)

    def complete_pending(self, outcome: str, valence: float) -> "Experience | None":
        pending = self._read_last_pending()
        if pending is None:
            logger.info("No pending experience to complete")
            return None
        self._remove_last_pending()
        return self.record(
            action=pending.action, context=pending.context,
            outcome=outcome, valence=valence,
            metadata=pending.metadata, parent_id=pending.parent_id,
        )

    def detect_valence(self, message: str) -> float:
        """Tiered valence detection: keyword -> LLM -> default."""
        keyword_result = self.detect_valence_keyword(message)
        if keyword_result is not None:
            return keyword_result
        if self._llm is not None:
            try:
                return self._llm.detect_valence(message)
            except Exception:
                logger.warning("LLM valence detection failed, using default")
        return 0.3

    def detect_valence_keyword(self, message: str) -> float | None:
        if POSITIVE_KEYWORDS.search(message):
            return 1.0
        if NEGATIVE_KEYWORDS.search(message):
            return -0.8
        if NEUTRAL_KEYWORDS.match(message.strip()):
            return 0.3
        return None

    def _locked_append(self, text: str) -> None:
        self._pending_path.parent.mkdir(parents=True, exist_ok=True)
        f = open(self._pending_path, "a", encoding="utf-8")
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(text)
            f.flush()
        finally:
            if sys.platform == "win32":
                import msvcrt
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except Exception:
                    pass
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            f.close()

    def _read_last_pending(self) -> Experience | None:
        if not self._pending_path or not self._pending_path.exists():
            return None
        lines = self._pending_path.read_text(encoding="utf-8").strip().split("\n")
        lines = [line for line in lines if line.strip()]
        if not lines:
            return None
        return Experience.model_validate_json(lines[-1])

    def _remove_last_pending(self) -> None:
        if not self._pending_path or not self._pending_path.exists():
            return
        lines = self._pending_path.read_text(encoding="utf-8").strip().split("\n")
        lines = [line for line in lines if line.strip()]
        if lines:
            lines.pop()
        self._pending_path.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")
