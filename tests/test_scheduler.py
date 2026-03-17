import asyncio
import pytest
from unittest.mock import MagicMock
from engram_ai.scheduler import Scheduler, SchedulerConfig


class FakeProjectManager:
    def __init__(self):
        self._forges = {}

    def add_forge(self, name, forge):
        self._forges[name] = forge

    def get_all_forges(self):
        return dict(self._forges)


def _make_mock_forge():
    forge = MagicMock()
    forge.apply_decay.return_value = []
    forge.detect_conflicts.return_value = []
    forge.crystallize.return_value = []
    forge._event_bus = MagicMock()
    return forge


@pytest.mark.asyncio
async def test_scheduler_start_stop():
    pm = FakeProjectManager()
    config = SchedulerConfig(decay_interval_hours=0.001, conflict_interval_hours=0.001)
    scheduler = Scheduler(pm, config)
    await scheduler.start()
    assert scheduler.is_running
    await scheduler.stop()
    assert not scheduler.is_running


@pytest.mark.asyncio
async def test_scheduler_disabled():
    pm = FakeProjectManager()
    config = SchedulerConfig(enabled=False)
    scheduler = Scheduler(pm, config)
    await scheduler.start()
    assert not scheduler.is_running


@pytest.mark.asyncio
async def test_decay_runs_on_all_projects():
    pm = FakeProjectManager()
    forge_a = _make_mock_forge()
    forge_b = _make_mock_forge()
    pm.add_forge("a", forge_a)
    pm.add_forge("b", forge_b)
    config = SchedulerConfig(decay_interval_hours=0.001, conflict_interval_hours=999)
    scheduler = Scheduler(pm, config)
    await scheduler.start()
    await asyncio.sleep(0.05)
    await scheduler.stop()
    forge_a.apply_decay.assert_called()
    forge_b.apply_decay.assert_called()


@pytest.mark.asyncio
async def test_conflict_runs_on_all_projects():
    pm = FakeProjectManager()
    forge_a = _make_mock_forge()
    pm.add_forge("a", forge_a)
    config = SchedulerConfig(decay_interval_hours=999, conflict_interval_hours=0.001)
    scheduler = Scheduler(pm, config)
    await scheduler.start()
    await asyncio.sleep(0.05)
    await scheduler.stop()
    forge_a.detect_conflicts.assert_called()


@pytest.mark.asyncio
async def test_crystallize_counter():
    pm = FakeProjectManager()
    forge = _make_mock_forge()
    pm.add_forge("proj", forge)
    config = SchedulerConfig(
        crystallize_threshold=2,
        decay_interval_hours=999,
        conflict_interval_hours=999,
    )
    scheduler = Scheduler(pm, config)
    await scheduler.start()
    scheduler.on_experience_recorded("proj")
    scheduler.on_experience_recorded("proj")
    await asyncio.sleep(0.05)
    await scheduler.stop()
    forge.crystallize.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_error_handling():
    """Scheduler continues after errors in individual projects."""
    pm = FakeProjectManager()
    forge = _make_mock_forge()
    forge.apply_decay.side_effect = RuntimeError("ChromaDB error")
    pm.add_forge("broken", forge)
    config = SchedulerConfig(decay_interval_hours=0.001, conflict_interval_hours=999)
    scheduler = Scheduler(pm, config)
    await scheduler.start()
    await asyncio.sleep(0.05)
    await scheduler.stop()
    # Should not raise — fail-open


def test_scheduler_status():
    pm = FakeProjectManager()
    config = SchedulerConfig()
    scheduler = Scheduler(pm, config)
    status = scheduler.get_status()
    assert "enabled" in status
    assert "crystallize_threshold" in status
