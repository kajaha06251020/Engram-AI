import pytest
from fastapi.testclient import TestClient

from engram_ai import Forge
from engram_ai.dashboard.server import create_app


@pytest.fixture
def forge(tmp_path, mock_llm):
    return Forge(storage_path=str(tmp_path / "test_db"), llm=mock_llm)


@pytest.fixture
def client(forge):
    app = create_app(forge=forge)
    return TestClient(app)


def test_websocket_receives_experience_event(client, forge):
    """Recording an experience pushes event to connected WebSocket."""
    with client.websocket_connect("/ws") as ws:
        forge.record(
            action="Test action",
            context="Test context",
            outcome="Test outcome",
            valence=0.5,
        )
        data = ws.receive_json()
        assert data["event"] == "experience.recorded"
        assert data["data"]["action"] == "Test action"


def test_websocket_disconnect_cleans_up_handlers(client, forge):
    """Disconnecting removes EventBus listeners."""
    initial = len(forge._event_bus._subscribers.get("experience.recorded", []))
    with client.websocket_connect("/ws"):
        pass
    current = len(forge._event_bus._subscribers.get("experience.recorded", []))
    assert current == initial
