import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from engram_ai.events.events import EXPERIENCE_RECORDED

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    decay_interval_hours: float = 6.0
    conflict_interval_hours: float = 12.0
    crystallize_threshold: int = 10
    enabled: bool = True


class Scheduler:
    """Global background scheduler for decay, conflict detection, and crystallize."""

    def __init__(self, project_manager, config: SchedulerConfig) -> None:
        self._pm = project_manager
        self._config = config
        self._tasks: list[asyncio.Task] = []
        self._running = False
        self._counters: dict[str, int] = {}
        self._last_decay: datetime | None = None
        self._last_conflict: datetime | None = None
        self._subscribed_projects: set[str] = set()

    @property
    def is_running(self) -> bool:
        return self._running

    def _subscribe_to_forges(self) -> None:
        """Subscribe to EXPERIENCE_RECORDED on all project EventBuses."""
        for name, forge in self._pm.get_all_forges().items():
            if name not in self._subscribed_projects:
                forge._event_bus.on(
                    EXPERIENCE_RECORDED,
                    lambda _payload, n=name: self.on_experience_recorded(n),
                )
                self._subscribed_projects.add(name)

    async def start(self) -> None:
        if not self._config.enabled:
            logger.info("Scheduler disabled, not starting")
            return
        self._running = True
        self._subscribe_to_forges()
        self._tasks.append(asyncio.create_task(self._decay_loop()))
        self._tasks.append(asyncio.create_task(self._conflict_loop()))
        logger.info("Scheduler started")

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        logger.info("Scheduler stopped")

    def on_experience_recorded(self, project: str) -> None:
        self._counters[project] = self._counters.get(project, 0) + 1
        if self._counters[project] >= self._config.crystallize_threshold:
            self._counters[project] = 0
            self._trigger_crystallize(project)

    def _trigger_crystallize(self, project: str) -> None:
        forges = self._pm.get_all_forges()
        forge = forges.get(project)
        if forge:
            try:
                forge.crystallize()
                logger.info("Auto-crystallize completed for project %s", project)
            except Exception:
                logger.exception("Crystallize failed for project %s", project)

    async def _decay_loop(self) -> None:
        interval = self._config.decay_interval_hours * 3600
        while self._running:
            self._last_decay = datetime.now()
            for name, forge in self._pm.get_all_forges().items():
                try:
                    forge.apply_decay()
                    logger.info("Decay applied for project %s", name)
                except Exception:
                    logger.exception("Decay failed for project %s", name)
            await asyncio.sleep(interval)

    async def _conflict_loop(self) -> None:
        interval = self._config.conflict_interval_hours * 3600
        while self._running:
            self._last_conflict = datetime.now()
            for name, forge in self._pm.get_all_forges().items():
                try:
                    forge.detect_conflicts()
                    logger.info("Conflict check completed for project %s", name)
                except Exception:
                    logger.exception("Conflict check failed for project %s", name)
            await asyncio.sleep(interval)

    def get_status(self) -> dict:
        next_decay = None
        next_conflict = None
        if self._running:
            now = datetime.now()
            if self._last_decay:
                next_decay = (self._last_decay + timedelta(hours=self._config.decay_interval_hours)).isoformat()
            else:
                next_decay = (now + timedelta(hours=self._config.decay_interval_hours)).isoformat()
            if self._last_conflict:
                next_conflict = (self._last_conflict + timedelta(hours=self._config.conflict_interval_hours)).isoformat()
            else:
                next_conflict = (now + timedelta(hours=self._config.conflict_interval_hours)).isoformat()
        return {
            "enabled": self._config.enabled,
            "running": self._running,
            "next_decay": next_decay,
            "next_conflict_check": next_conflict,
            "crystallize_threshold": self._config.crystallize_threshold,
            "experience_counts": dict(self._counters),
        }
