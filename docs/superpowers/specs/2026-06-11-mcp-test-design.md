# bss-mcp test design

**Date:** 2026-06-11  
**Status:** approved

## Context

bss-mcp is a FastMCP-based MCP server that wraps the `bssclient` library (Hochfrequenz). The `bssclient` package exposes a typed async client (`BssClient` ABC) with four methods returning Pydantic models. The server exposes these as MCP tools for read-only debug use.

The test strategy must be stable over years as `bssclient` evolves, maintainable by multiple developers, and aligned with the official FastMCP testing documentation.

## Decision: `AsyncMock(spec=BssClient)` with factory pattern

Three approaches were evaluated:

| Approach | Type boundary | Verdict |
|---|---|---|
| A — `AsyncMock(spec=BssClient)` | `BssClient` ABC | **Chosen** |
| B — `BssClientProtocol(Protocol)` | Server-owned Protocol | Rejected |
| C — `DummyBssClient(BasicAuthBssClient)` | Concrete subclass | Rejected |

**Why A:** `BssClient` is already the versioned interface maintained by upstream. `spec=BssClient` gives immediate `AttributeError` when methods are added, removed, or renamed — the mock tracks the real interface at test time. No secondary artifact drifts silently. Zero extra files to maintain.

**Why not B:** A structural `Protocol` duplicates the upstream ABC. When `bssclient` evolves and a new server tool is added, three places must be updated (tool, Protocol, test). Protocol drift is silent — mypy will not catch it if `BssClientProtocol` becomes a stale subset of `BssClient`.

**Why not C:** `DummyBssClient` subclasses a concrete implementation (`BasicAuthBssClient`), not the contract. Constructor changes or initialization side-effects in the concrete class break tests for reasons unrelated to server logic.

## Architecture

```
src/bss_mcp/
  __init__.py
  server.py       ← create_server(client: BssClient) -> FastMCP  +  main()
  settings.py     ← pydantic-settings: reads env vars, builds BssClient

unittests/
  __init__.py
  conftest.py     ← mock_bss_client fixture, bss_server fixture, test data builders
  test_smoke.py   ← import check (exists)
  test_server.py  ← one happy-path + one error-path test per tool; one tool-list test
```

### `server.py` shape

```python
from bssclient.client.bssclient import BssClient
from fastmcp import FastMCP


def create_server(client: BssClient) -> FastMCP:
    mcp = FastMCP("bss-mcp")

    @mcp.tool
    async def get_ermittlungsauftraege() -> list[...]:
        return await client.get_ermittlungsauftraege()

    # ... remaining tools

    return mcp


def main() -> None:
    # read settings, build real client, run server
    ...
```

`create_server` is a pure function with no I/O. `main()` is the only entry point that touches the environment.

### `settings.py` shape

Pydantic-settings model that reads from env vars (already documented in `.env.example`): `BSS_URL`, `BSS_AUTH_TYPE`, `BSS_USER`, `BSS_PASSWORD` / `BSS_CLIENT_ID`, `BSS_CLIENT_SECRET`, `BSS_TOKEN_URL`. Builds and returns either `BasicAuthBssClient` or `OAuthBssClient`.

## Test structure

### `conftest.py`

```python
import pytest
from unittest.mock import AsyncMock
from fastmcp import FastMCP
from bssclient.client.bssclient import BssClient
from bss_mcp.server import create_server


@pytest.fixture
def mock_bss_client() -> AsyncMock:
    return AsyncMock(spec=BssClient)


@pytest.fixture
def bss_server(mock_bss_client: AsyncMock) -> FastMCP:
    return create_server(mock_bss_client)


# Minimal test-data builders — only required Pydantic fields
def build_ermittlungsauftrag(...) -> Ermittlungsauftrag: ...
def build_aufgabe_stats(...) -> AufgabeStats: ...
```

The `Client` context is never opened inside a fixture (FastMCP docs: opening clients in fixtures causes hard-to-diagnose event-loop issues). Each test opens its own `async with Client(bss_server)`.

### `test_server.py` — pattern per tool

```python
from fastmcp import Client

async def test_get_ermittlungsauftraege_returns_list(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_ermittlungsauftraege.return_value = [build_ermittlungsauftrag()]
    async with Client(bss_server) as client:
        result = await client.call_tool("get_ermittlungsauftraege", {})
    assert len(result.data) == 1
    mock_bss_client.get_ermittlungsauftraege.assert_awaited_once_with()


async def test_get_ermittlungsauftraege_propagates_client_error(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_ermittlungsauftraege.side_effect = Exception("BSS unavailable")
    async with Client(bss_server) as client:
        with pytest.raises(Exception, match="BSS unavailable"):
            await client.call_tool("get_ermittlungsauftraege", {})
```

Every test asserts both the result **and** `assert_awaited_once_with(...)` on the mock. This ensures a tool that forgets to call the client cannot silently pass.

### Tool list test

```python
async def test_server_exposes_expected_tools(bss_server: FastMCP) -> None:
    async with Client(bss_server) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == {
        "get_ermittlungsauftraege",
        "get_ermittlungsauftraege_by_malo",
        "get_aufgabe_stats",
        "get_all_ermittlungsauftraege",
    }
```

This test is the canary for accidental tool renames.

## Tools to implement

Based on `BssClient` public API:

| MCP tool name | Wraps | Arguments | Return |
|---|---|---|---|
| `get_ermittlungsauftraege` | `get_ermittlungsauftraege(limit, offset)` | `limit: int = 0`, `offset: int = 0` | `list[Ermittlungsauftrag]` |
| `get_ermittlungsauftraege_by_malo` | `get_ermittlungsauftraege_by_malo(malo_id)` | `malo_id: str` | `list[Ermittlungsauftrag]` |
| `get_aufgabe_stats` | `get_aufgabe_stats()` | — | `AufgabeStats` |
| `get_all_ermittlungsauftraege` | `get_all_ermittlungsauftraege(package_size)` | `package_size: int = 100` | `list[Ermittlungsauftrag]` |

## Error handling

Each tool wraps the client call in a try/except and propagates the exception. FastMCP surfaces it as a tool error to the MCP client. Tests verify propagation with `side_effect`.

## Coverage

With `create_server` as a pure function and one happy-path + one error-path per tool, `server.py` coverage will comfortably exceed 80% with no exclusions needed.

## Dependencies

No new test dependencies beyond the existing `tests` optional group (`pytest>=9`, `pytest-asyncio>=0.24`, `pytest-mock>=3`). `AsyncMock` is stdlib (`unittest.mock`). `fastmcp` is already a runtime dep.
