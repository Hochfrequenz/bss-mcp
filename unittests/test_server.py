"""Tests for bss_mcp.server."""
import pytest
from unittest.mock import AsyncMock
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from bssclient.client.bssclient import BssClient
from bss_mcp.server import create_server
from unittests.conftest import build_aufgabe_stats, build_ermittlungsauftrag


async def test_server_exposes_expected_tools(bss_server: FastMCP) -> None:
    async with Client(bss_server) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == {
        "get_ermittlungsauftraege",
        "get_ermittlungsauftraege_by_malo",
        "get_aufgabe_stats",
        "get_all_ermittlungsauftraege",
    }


async def test_get_ermittlungsauftraege_returns_list(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    ea = build_ermittlungsauftrag()
    mock_bss_client.get_ermittlungsauftraege.return_value = [ea]
    async with Client(bss_server) as client:
        result = await client.call_tool("get_ermittlungsauftraege", {})
    assert result.data is not None
    assert len(result.data) == 1
    mock_bss_client.get_ermittlungsauftraege.assert_awaited_once_with(limit=0, offset=0)


async def test_get_ermittlungsauftraege_forwards_limit_offset(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_ermittlungsauftraege.return_value = []
    async with Client(bss_server) as client:
        result = await client.call_tool(
            "get_ermittlungsauftraege", {"limit": 10, "offset": 5}
        )
    assert result.data is not None
    mock_bss_client.get_ermittlungsauftraege.assert_awaited_once_with(limit=10, offset=5)


async def test_get_ermittlungsauftraege_propagates_error(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_ermittlungsauftraege.side_effect = Exception("BSS unavailable")
    async with Client(bss_server) as client:
        with pytest.raises(ToolError, match="BSS unavailable"):
            await client.call_tool("get_ermittlungsauftraege", {})
