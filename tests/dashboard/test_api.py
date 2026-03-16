import pytest
from fastapi.testclient import TestClient

from engram_ai import Forge
from engram_ai.dashboard.server import create_app
from engram_ai.models.skill import Skill


@pytest.fixture
def forge(tmp_path, mock_llm):
    return Forge(storage_path=str(tmp_path / "test_db"), llm=mock_llm)


@pytest.fixture
def client(forge):
    app = create_app(forge=forge)
    return TestClient(app)


@pytest.fixture
def seeded_forge(tmp_path, mock_llm):
    forge = Forge(storage_path=str(tmp_path / "test_db"), llm=mock_llm)
    exp1 = forge.record(
        action="Used list comprehension",
        context="Data processing",
        outcome="Fast and readable",
        valence=0.9,
    )
    forge.record(
        action="Skipped type hints",
        context="Utility functions",
        outcome="Hard to maintain",
        valence=-0.7,
    )
    exp3 = forge.record(
        action="Added tests first",
        context="New feature",
        outcome="Caught bugs early",
        valence=0.8,
    )
    skill = Skill(
        rule="Prefer list comprehensions for data transforms",
        context_pattern="Data processing",
        confidence=0.85,
        source_experiences=[exp1.id, exp3.id],
        evidence_count=2,
        valence_summary={"positive": 2, "negative": 0},
    )
    forge._storage.store_skill(skill)
    return forge


@pytest.fixture
def seeded_client(seeded_forge):
    app = create_app(forge=seeded_forge)
    return TestClient(app)


def test_status_returns_counts(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert data["total_experiences"] == 0
    assert data["total_skills"] == 0
    assert data["unapplied_skills"] == 0


def test_status_reflects_data(seeded_client):
    data = seeded_client.get("/api/status").json()
    assert data["total_experiences"] == 3
    assert data["total_skills"] == 1


def test_experiences_empty(client):
    r = client.get("/api/experiences")
    assert r.status_code == 200
    assert r.json() == []


def test_experiences_returns_all(seeded_client):
    data = seeded_client.get("/api/experiences").json()
    assert len(data) == 3


def test_search_returns_best_and_avoid(seeded_client):
    r = seeded_client.get("/api/experiences/search?q=data+processing")
    assert r.status_code == 200
    data = r.json()
    assert "best" in data
    assert "avoid" in data
    for item in data["best"] + data["avoid"]:
        assert "experience" in item
        assert "score" in item


def test_skills_returns_with_applied_status(seeded_client):
    data = seeded_client.get("/api/skills").json()
    assert len(data) == 1
    assert "applied" in data[0]
    assert data[0]["applied"] is False


def test_graph_returns_nodes_and_edges(seeded_client):
    data = seeded_client.get("/api/graph").json()
    assert "nodes" in data
    assert "edges" in data
    node_types = {n["type"] for n in data["nodes"]}
    assert "experience" in node_types
    assert "skill" in node_types


def test_crystallize_returns_list(seeded_client):
    r = seeded_client.post("/api/crystallize", json={})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_evolve_returns_record_or_null(seeded_client):
    r = seeded_client.post("/api/evolve", json={"config_path": "./test_CLAUDE.md"})
    assert r.status_code == 200
