# bss-mcp

![Unittests status badge](https://github.com/Hochfrequenz/bss-mcp/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/bss-mcp/workflows/Coverage/badge.svg)
![Linting status badge](https://github.com/Hochfrequenz/bss-mcp/workflows/Linting/badge.svg)
![Black status badge](https://github.com/Hochfrequenz/bss-mcp/workflows/Formatting/badge.svg)

An [MCP](https://modelcontextprotocol.io/) server wrapping [`bssclient`](https://github.com/Hochfrequenz/bssclient.py) — read-only debug tooling for the Basic Supply Service (BSS).

## Tools

| Tool | Description |
|---|---|
| `get_ermittlungsauftraege` | List investigation orders (`limit`, `offset`) |
| `get_ermittlungsauftraege_by_malo` | Investigation orders for a Marktlokation ID |
| `get_aufgabe_stats` | Task status statistics across all Aufgaben types |
| `get_all_ermittlungsauftraege` | All investigation orders via paginated fetch |

## Installation

```bash
pip install bss-mcp
```

## Configuration

Set environment variables (or place them in a `.env` file):

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

Or add to your MCP client config (e.g. Claude Desktop):

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

This project follows the [Hochfrequenz Python template](https://github.com/Hochfrequenz/python_template_repository) — see it for general setup instructions (tox, CI, PyPI publishing).

```bash
tox -e tests       # run tests
tox -e type_check  # mypy --strict
tox -e linting     # pylint
tox -e coverage    # coverage ≥ 80 %
```

The BSS client library is provided by [`bssclient`](https://github.com/Hochfrequenz/bssclient.py).
