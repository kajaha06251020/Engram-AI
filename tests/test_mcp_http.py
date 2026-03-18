import pytest
pytest.importorskip("mcp", reason="mcp extra not installed: pip install engram-ai[mcp]")
pytest.importorskip("starlette", reason="starlette not installed")
pytest.importorskip("httpx", reason="httpx not installed: pip install httpx")

from unittest.mock import patch
from starlette.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    """Create a TestClient with lifespan activated (starts session_manager)."""
    with patch.dict("os.environ", {"ENGRAM_AI_STORAGE": str(tmp_path / "data")}):
        from engram_ai.mcp import create_http_app
        app = create_http_app()
        with TestClient(app) as c:
            yield c


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_mcp_endpoint_exists(client):
    """POST /mcp should not return 404 (proves Route works, not Mount)."""
    resp = client.post("/mcp", json={})
    # MCP server will return an error for invalid JSON-RPC, but NOT 404
    assert resp.status_code != 404


def test_mcp_endpoint_rejects_get(client):
    """GET /mcp is not a valid MCP operation."""
    resp = client.get("/mcp")
    assert resp.status_code in (400, 405, 406)
