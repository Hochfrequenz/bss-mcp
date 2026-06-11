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
