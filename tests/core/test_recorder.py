import json
import pytest
from engram_ai.models.experience import Experience

@pytest.fixture
def storage(tmp_path):
    from engram_ai.storage.chromadb import ChromaDBStorage
    return ChromaDBStorage(persist_path=str(tmp_path / "db"))

@pytest.fixture
def bus():
    from engram_ai.events.bus import EventBus
    return EventBus()

@pytest.fixture
def recorder(storage, bus, tmp_path):
    from engram_ai.core.recorder import Recorder
    return Recorder(storage=storage, event_bus=bus, pending_path=str(tmp_path / "pending.jsonl"))

def test_record_complete_experience(recorder, storage):
    recorder.record(action="test action", context="test context", outcome="test outcome", valence=0.8)
    experiences = storage.get_all_experiences()
    assert len(experiences) == 1
    assert experiences[0].action == "test action"
    assert experiences[0].status == "complete"

def test_record_emits_event(recorder, bus):
    received = []
    bus.on("experience.recorded", lambda p: received.append(p))
    recorder.record(action="a", context="c", outcome="o", valence=0.5)
    assert len(received) == 1
    assert received[0].action == "a"

def test_record_pending_experience(recorder, tmp_path):
    recorder.record_pending(action="edited file", context="coding session", metadata={"tool": "Edit"})
    pending_path = tmp_path / "pending.jsonl"
    assert pending_path.exists()
    lines = pending_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["action"] == "edited file"
    assert data["status"] == "pending"

def test_complete_pending_experience(recorder, storage, tmp_path):
    recorder.record_pending(action="edited file", context="coding session", metadata={})
    recorder.complete_pending(outcome="user approved", valence=1.0)
    experiences = storage.get_all_experiences()
    assert len(experiences) == 1
    assert experiences[0].outcome == "user approved"
    assert experiences[0].valence == 1.0
    assert experiences[0].status == "complete"

def test_complete_pending_with_no_pending(recorder, storage):
    recorder.complete_pending(outcome="no pending", valence=0.5)
    assert storage.get_all_experiences() == []

def test_valence_keyword_detection(recorder):
    assert recorder.detect_valence_keyword("完璧です！") > 0.5
    assert recorder.detect_valence_keyword("perfect, thanks") > 0.5
    assert recorder.detect_valence_keyword("違う、やり直して") < -0.5
    assert recorder.detect_valence_keyword("wrong, fix this") < -0.5
    assert recorder.detect_valence_keyword("some random text") is None
