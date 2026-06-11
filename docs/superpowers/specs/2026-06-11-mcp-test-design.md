# bss-mcp test design

**Date:** 2026-06-11  
**Status:** approved

## Context

bss-mcp is a FastMCP-based MCP server that wraps the `bssclient` library (Hochfrequenz). The `bssclient` package exposes a typed async client (`BssClient` ABC) with methods returning Pydantic models. The server exposes a read-only subset of these as MCP tools for debug use.

The test strategy must be stable over years as `bssclient` evolves, maintainable by multiple developers, and aligned with the official FastMCP testing documentation.

## Decision: `AsyncMock(spec=BssClient)` with factory pattern

Three approaches were evaluated:

| Approach | Type boundary | Verdict |
|---|---|---|
| A — `AsyncMock(spec=BssClient)` | `BssClient` ABC | **Chosen** |
| B — `BssClientProtocol(Protocol)` | Server-owned Protocol | Rejected |
| C — `DummyBssClient(BasicAuthBssClient)` | Concrete subclass | Rejected |

**Why A:** `BssClient` is already the versioned interface maintained by upstream. `spec=BssClient` gives immediate `AttributeError` when methods are added, removed, or renamed — the mock tracks the real interface at test time. No secondary artifact drifts silently. Zero extra files to maintain. `AsyncMock(spec=BssClient)` is safe to instantiate: `BssClient.__init__` only creates an `asyncio.Lock` and sets `_session = None` — no network connections, no event-loop dependency at construction time.

**Why not B:** A structural `Protocol` duplicates the upstream ABC. When `bssclient` evolves and a new server tool is added, three places must be updated (tool, Protocol, test). Protocol drift is silent — mypy will not catch it if `BssClientProtocol` becomes a stale subset of `BssClient`.

**Why not C:** `DummyBssClient` subclasses a concrete implementation (`BasicAuthBssClient`), not the contract. Constructor changes or initialization side-effects in the concrete class break tests for reasons unrelated to server logic.

## Scope: which `BssClient` methods become tools

`BssClient` exposes six async public methods. This server is **read-only debug tooling**, so:

| Method | Included | Reason |
|---|---|---|
| `get_ermittlungsauftraege(limit, offset)` | Yes | read-only |
| `get_ermittlungsauftraege_by_malo(malo_id)` | Yes | read-only |
| `get_aufgabe_stats()` | Yes | read-only |
| `get_all_ermittlungsauftraege(package_size)` | Yes | read-only convenience wrapper |
| `get_events(model_type, model_id)` | No | not yet needed for debug use cases; add when required |
| `replay_event(model_type, model_id, event_number)` | No | mutates state — violates read-only contract |

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
    async def get_ermittlungsauftraege(
        limit: int = 0, offset: int = 0
    ) -> list[Ermittlungsauftrag]:
        return await client.get_ermittlungsauftraege(limit=limit, offset=offset)

    # ... remaining tools

    return mcp


def main() -> None:
    # read settings, build real client, run server
    ...
```

`create_server` is a pure function with no I/O. `main()` is the only entry point that touches the environment.

**Typing principle:** MCP tool signatures are typed exactly as the underlying `BssClient` methods — same parameter types, same return types (Pydantic models). No `dict`, no `Any`, no raw JSON anywhere in the tool interface.

### `settings.py` shape

Pydantic-settings model that reads from env vars (documented in `.env.example`): `BSS_URL`, `BSS_AUTH_TYPE`, `BSS_USER`, `BSS_PASSWORD` / `BSS_CLIENT_ID`, `BSS_CLIENT_SECRET`, `BSS_TOKEN_URL`. Builds and returns either `BasicAuthBssClient` or `OAuthBssClient`.

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
    # FastMCP.__init__ is synchronous — safe in a sync fixture
    return create_server(mock_bss_client)


# Minimal Pydantic builders — only required fields
def build_ermittlungsauftrag(...) -> Ermittlungsauftrag: ...
def build_aufgabe_stats(...) -> AufgabeStats: ...
```

The `Client` context is **never** opened inside a fixture (FastMCP docs: opening clients in fixtures causes hard-to-diagnose event-loop issues). Each test opens its own `async with Client(bss_server)`.

### `test_server.py` — pattern per tool

`result.data` is populated because FastMCP infers a JSON schema from the typed return annotation and wraps/unwraps the result automatically. A missing or `Any` return annotation would leave `.data` as `None` and cause a confusing `TypeError` — this is why all tool return types must be explicit Pydantic models.

```python
from fastmcp import Client
from fastmcp.exceptions import ToolError


async def test_get_ermittlungsauftraege_returns_list(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_ermittlungsauftraege.return_value = [build_ermittlungsauftrag()]
    async with Client(bss_server) as client:
        result = await client.call_tool("get_ermittlungsauftraege", {})
    assert result.data is not None
    assert len(result.data) == 1
    mock_bss_client.get_ermittlungsauftraege.assert_awaited_once_with(limit=0, offset=0)


async def test_get_ermittlungsauftraege_by_malo(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_ermittlungsauftraege_by_malo.return_value = [build_ermittlungsauftrag()]
    async with Client(bss_server) as client:
        result = await client.call_tool(
            "get_ermittlungsauftraege_by_malo", {"malo_id": "DE0001234567890"}
        )
    assert result.data is not None
    # Argument must appear in the assertion — verifies the server forwarded it correctly
    mock_bss_client.get_ermittlungsauftraege_by_malo.assert_awaited_once_with(
        malo_id="DE0001234567890"
    )


async def test_get_all_ermittlungsauftraege_passes_package_size(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_all_ermittlungsauftraege.return_value = []
    async with Client(bss_server) as client:
        result = await client.call_tool(
            "get_all_ermittlungsauftraege", {"package_size": 50}
        )
    assert result.data is not None
    # Note: the server delegates to the client — it does NOT inline pagination logic.
    # The real pagination lives in bssclient; this test verifies delegation only.
    mock_bss_client.get_all_ermittlungsauftraege.assert_awaited_once_with(package_size=50)


async def test_get_ermittlungsauftraege_propagates_client_error(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_ermittlungsauftraege.side_effect = Exception("BSS unavailable")
    async with Client(bss_server) as client:
        # FastMCP converts tool exceptions to ToolError on the client side
        with pytest.raises(ToolError, match="BSS unavailable"):
            await client.call_tool("get_ermittlungsauftraege", {})
```

Every test asserts both the result **and** the mock call with full arguments. A tool that forgets to forward a parameter cannot silently pass.

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

This test is the canary for accidental tool renames or additions.

## Tools to implement

| MCP tool name | Wraps | Arguments | Return |
|---|---|---|---|
| `get_ermittlungsauftraege` | `get_ermittlungsauftraege(limit, offset)` | `limit: int = 0`, `offset: int = 0` | `list[Ermittlungsauftrag]` |
| `get_ermittlungsauftraege_by_malo` | `get_ermittlungsauftraege_by_malo(malo_id)` | `malo_id: str` | `list[Ermittlungsauftrag]` |
| `get_aufgabe_stats` | `get_aufgabe_stats()` | — | `AufgabeStats` |
| `get_all_ermittlungsauftraege` | `get_all_ermittlungsauftraege(package_size)` | `package_size: int = 100` | `list[Ermittlungsauftrag]` |

## Error handling

Each tool propagates exceptions from the client without wrapping. FastMCP converts them to `ToolError` on the client side. Tests use `pytest.raises(ToolError, match=...)`.

## Coverage

With `create_server` as a pure function and one happy-path + one error-path per tool, `server.py` coverage will exceed 80% with no exclusions needed.

## Dependencies

No new test dependencies beyond the existing `tests` optional group (`pytest>=9`, `pytest-asyncio>=0.24`, `pytest-mock>=3`). `AsyncMock` is stdlib. `ToolError` is from `fastmcp.exceptions`, already a runtime dep. `fastmcp` is already a runtime dep.
