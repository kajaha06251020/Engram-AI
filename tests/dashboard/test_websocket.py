import pytest
from fastapi.testclient import TestClient

from engram_ai.dashboard.server import create_app


@pytest.fixture
def forge(tmp_path, mock_llm):
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, llm=mock_llm, config={"default_project": "default"})
    return pm.get_forge("default")


@pytest.fixture
def client(tmp_path, mock_llm):
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, llm=mock_llm, config={"default_project": "default"})
    app = create_app(project_manager=pm)
    return TestClient(app)


@pytest.fixture
def forge_and_client(tmp_path, mock_llm):
    """Shared fixture that returns (forge, client) backed by the same ProjectManager."""
    from engram_ai.project import ProjectManager
    pm = ProjectManager(base_path=tmp_path, llm=mock_llm, config={"default_project": "default"})
    forge = pm.get_forge("default")
    app = create_app(project_manager=pm)
    return forge, TestClient(app)


def test_websocket_receives_experience_event(forge_and_client):
    """Recording an experience pushes event to connected WebSocket."""
    forge, client = forge_and_client
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


def test_websocket_disconnect_cleans_up_handlers(forge_and_client):
    """Disconnecting removes EventBus listeners."""
    forge, client = forge_and_client
    initial = len(forge._event_bus._subscribers.get("experience.recorded", []))
    with client.websocket_connect("/ws"):
        pass
    current = len(forge._event_bus._subscribers.get("experience.recorded", []))
    assert current == initial
