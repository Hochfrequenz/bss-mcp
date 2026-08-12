# bss-mcp

MCP server wrapping the `bssclient` library for read-only BSS (Basic Supply Service) debug tooling.

## Core principle: typed all the way down

MCP tool signatures mirror the underlying `BssClient` methods exactly — same parameter types, same Pydantic return types. No `dict`, no `Any`, no raw JSON in tool interfaces. If `bssclient` returns `list[Ermittlungsauftrag]`, the tool returns `list[Ermittlungsauftrag]`. FastMCP uses the type annotations to generate the tool schema and to populate `result.data` on the client side — a missing or `Any` annotation breaks schema generation silently.

## Server structure

- `src/bss_mcp/server.py` — `create_server(client: BssClient) -> FastMCP` factory (pure, no I/O) + `main()` entry point
- `src/bss_mcp/settings.py` — pydantic-settings reading env vars, building `BasicAuthBssClient` or `OAuthBssClient`

`create_server` is the seam for tests: tests call it with `AsyncMock(spec=BssClient)`, production calls it with the real client.

## Testing

Tests use the official FastMCP in-process pattern:

```python
async with Client(create_server(mock_client)) as client:
    result = await client.call_tool("tool_name", {...})
```

Mock strategy: `AsyncMock(spec=BssClient)` — never a Protocol, never a concrete subclass. See `docs/superpowers/specs/2026-06-11-mcp-test-design.md` for full rationale.

Every test asserts both `result.data` and `mock.method.assert_awaited_once_with(...)` with explicit arguments. A tool that forgets to forward a parameter must not silently pass.

Tool exceptions propagate as `fastmcp.exceptions.ToolError` on the client side — use `pytest.raises(ToolError, match=...)` in error-path tests.

## Read-only scope

The server only exposes read-only `BssClient` methods. `replay_event` (mutates state) is excluded permanently. `get_events` is deferred — add when a concrete debug use case arises.

## CI

Dev tooling uses [uv](https://docs.astral.sh/uv/). Install everything with `uv sync --group dev`.
The `PYTHONPATH=src` prefix makes the `src` layout importable.

```
PYTHONPATH=src uv run --group tests pytest                                            # pytest
PYTHONPATH=src uv run --group type_check mypy --show-error-codes src/bss_mcp --strict # mypy --strict
PYTHONPATH=src uv run --group linting ruff check .                                    # ruff (lint)
PYTHONPATH=src uv run --group coverage coverage run -m pytest                         # coverage ≥ 80%
uv run --group linting ruff format .                                                  # ruff (format)
```
