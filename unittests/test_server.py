"""Tests for bss_mcp.server."""
import pytest
from unittest.mock import AsyncMock
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from bssclient.client.bssclient import BssClient
from bss_mcp.server import create_server
