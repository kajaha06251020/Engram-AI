import pytest
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from engram_ai.forge import Forge
from engram_ai.mcp import create_mcp_server
from tests.conftest import MockLLM


@pytest.fixture
def forge_and_server(tmp_path):
    forge = Forge(
        storage_path=str(tmp_path / "data"),
        llm=MockLLM(),
    )
    server = create_mcp_server(forge)
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
