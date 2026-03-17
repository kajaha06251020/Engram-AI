import pytest
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from engram_ai.forge import Forge
from engram_ai.mcp import create_mcp_server
from tests.conftest import MockLLM


class _SingleForgeProjectManager:
    """Minimal project-manager shim for unit tests."""

    def __init__(self, forge: Forge):
        self._forge = forge

    def get_forge(self, project=None) -> Forge:
        return self._forge


@pytest.fixture
def forge_and_server(tmp_path):
    forge = Forge(
        storage_path=str(tmp_path / "data"),
        llm=MockLLM(),
    )
    pm = _SingleForgeProjectManager(forge)
    server = create_mcp_server(pm)
    return forge, server


async def _list_tools(server):
    handler = server.request_handlers[ListToolsRequest]
    result = await handler(ListToolsRequest(method="tools/list"))
    return result.root.tools


async def _call_tool(server, name: str, arguments: dict):
    handler = server.request_handlers[CallToolRequest]
    result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name=name, arguments=arguments),
        )
    )
    return result.root.content


@pytest.mark.asyncio
async def test_list_tools(forge_and_server):
    _, server = forge_and_server
    tools = await _list_tools(server)
    tool_names = [t.name for t in tools]
    assert "engram_record" in tool_names
    assert "engram_query" in tool_names
    assert "engram_crystallize" in tool_names
    assert "engram_evolve" in tool_names
    assert "engram_status" in tool_names


@pytest.mark.asyncio
async def test_call_engram_status(forge_and_server):
    _, server = forge_and_server
    result = await _call_tool(server, "engram_status", {})
    assert result[0].text
    assert "Experiences:" in result[0].text


@pytest.mark.asyncio
async def test_call_engram_record(forge_and_server):
    _, server = forge_and_server
    result = await _call_tool(server, "engram_record", {
        "action": "test",
        "context": "ctx",
        "outcome": "out",
        "valence": 0.5,
    })
    assert "Recorded" in result[0].text


@pytest.mark.asyncio
async def test_engram_conflicts(forge_and_server):
    _, server = forge_and_server
    result = await _call_tool(server, "engram_conflicts", {})
    assert result[0].text  # Should return text output


@pytest.mark.asyncio
async def test_engram_decay(forge_and_server):
    _, server = forge_and_server
    result = await _call_tool(server, "engram_decay", {})
    assert result[0].text


@pytest.mark.asyncio
async def test_list_tools_includes_v02(forge_and_server):
    _, server = forge_and_server
    tools = await _list_tools(server)
    tool_names = [t.name for t in tools]
    assert "engram_conflicts" in tool_names
    assert "engram_merge" in tool_names
    assert "engram_decay" in tool_names


@pytest.mark.asyncio
async def test_list_tools_includes_observe(forge_and_server):
    _, server = forge_and_server
    tools = await _list_tools(server)
    tool_names = [t.name for t in tools]
    assert "engram_observe" in tool_names


@pytest.mark.asyncio
async def test_engram_observe_no_experience(forge_and_server):
    forge, server = forge_and_server
    result = await _call_tool(server, "engram_observe", {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
    })
    assert "No notable experience" in result[0].text


@pytest.mark.asyncio
async def test_engram_observe_records(forge_and_server):
    forge, server = forge_and_server
    forge._llm.set_extract_experience_response({
        "action": "Fixed auth bug",
        "context": "Login was broken",
        "outcome": "Login works now",
        "valence": 0.9,
    })
    result = await _call_tool(server, "engram_observe", {
        "messages": [
            {"role": "user", "content": "Login is broken"},
            {"role": "assistant", "content": "Fixed the auth middleware"},
        ],
    })
    assert "Recorded" in result[0].text
    assert "Fixed auth bug" in result[0].text


@pytest.mark.asyncio
async def test_engram_observe_empty_messages(forge_and_server):
    _, server = forge_and_server
    result = await _call_tool(server, "engram_observe", {"messages": []})
    assert "No notable experience" in result[0].text
