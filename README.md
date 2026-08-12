# bss-mcp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python Versions (officially) supported](https://img.shields.io/pypi/pyversions/bss-mcp.svg)
![Pypi status badge](https://img.shields.io/pypi/v/bss-mcp)
![Unittests status badge](https://github.com/Hochfrequenz/bss-mcp/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/bss-mcp/workflows/Coverage/badge.svg)
![Linting status badge](https://github.com/Hochfrequenz/bss-mcp/workflows/Linting/badge.svg)
![Black status badge](https://github.com/Hochfrequenz/bss-mcp/workflows/Formatting/badge.svg)

An [MCP](https://modelcontextprotocol.io/) server wrapping [`bssclient`](https://github.com/Hochfrequenz/bssclient.py), exposing read-only BSS investigation-order data to AI assistants (e.g. Claude Desktop) for debugging.

Requires **Python 3.11+**.

## Tools

| Tool | Description |
|---|---|
| `get_ermittlungsauftraege` | List investigation orders (`limit`, `offset`; `limit=0` uses the server default) |
| `get_ermittlungsauftraege_by_malo` | Investigation orders for a Marktlokation ID |
| `get_aufgabe_stats` | Task status statistics across all Aufgaben types |
| `get_all_ermittlungsauftraege` | Fetches all investigation orders by iterating pages (`package_size` controls page size, default 100) |

## Installation

```bash
pip install bss-mcp
```

For use with [Claude Desktop](https://claude.ai/download) or another MCP client, `pipx` installs the server as a standalone executable:

```bash
pipx install bss-mcp
```

## Configuration

Set environment variables or place them in a `.env` file in the working directory from which the MCP server is launched (for Claude Desktop this is typically the user's home directory):

| Variable | Required | Description |
|---|---|---|
| `BSS_URL` | Yes | Base URL of the BSS server, e.g. `https://basicsupply.example.de/` |
| `BSS_AUTH_TYPE` | No (default: `basic`) | `basic` or `oauth` |
| `BSS_USER` | If basic auth | Username |
| `BSS_PASSWORD` | If basic auth | Password |
| `BSS_CLIENT_ID` | If OAuth | OAuth client ID |
| `BSS_CLIENT_SECRET` | If OAuth | OAuth client secret |
| `BSS_TOKEN_URL` | If OAuth | Token endpoint URL |

## Usage

Run the server directly:

```bash
bss-mcp
```

Or add to your MCP client config (e.g. Claude Desktop). Use the full path to the executable if `bss-mcp` is not on the PATH seen by the client:

```json
{
  "mcpServers": {
    "bss": {
      "command": "bss-mcp",
      "env": {
        "BSS_URL": "https://basicsupply.example.de/",
        "BSS_AUTH_TYPE": "basic",
        "BSS_USER": "...",
        "BSS_PASSWORD": "..."
      }
    }
  }
}
```

## Development

This project follows the [Hochfrequenz Python template](https://github.com/Hochfrequenz/python_template_repository) — see it for general setup instructions (uv, CI, PyPI publishing).

Install the dev dependencies with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --group dev
```

Common tasks (the `PYTHONPATH=src` prefix makes the `src` layout importable):

```bash
PYTHONPATH=src uv run --group tests pytest                                            # run tests
PYTHONPATH=src uv run --group type_check mypy --show-error-codes src/bss_mcp --strict # mypy --strict
PYTHONPATH=src uv run --group linting pylint bss_mcp                                  # pylint
PYTHONPATH=src uv run --group coverage coverage run -m pytest                         # coverage (≥ 80 %)
uv run --group formatting black .                                                     # format with black
uv run --group formatting isort .                                                     # sort imports with isort
```
