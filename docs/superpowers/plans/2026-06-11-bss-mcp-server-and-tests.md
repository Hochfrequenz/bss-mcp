# bss-mcp Server and Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `create_server(client: BssClient) -> FastMCP`, `settings.py`, and a full test suite covering all four MCP tools with happy-path and error-path tests.

**Architecture:** `create_server` is a pure function (no I/O) that registers four typed MCP tools wrapping `BssClient`. `settings.py` reads env vars via pydantic-settings and builds the real `BssClient`. Tests use `AsyncMock(spec=BssClient)` + FastMCP's official in-process `Client` for full integration with zero network I/O.

**Tech Stack:** Python 3.11+, FastMCP ≥3.0, bssclient, pydantic-settings, pytest-asyncio, stdlib `unittest.mock.AsyncMock`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/bss_mcp/server.py` | `create_server(client) -> FastMCP` + `main()` |
| Create | `src/bss_mcp/settings.py` | Env-var config → `BssClient` factory |
| Create | `unittests/conftest.py` | Shared fixtures + Pydantic test-data builders |
| Create | `unittests/test_server.py` | All tool tests (tool-list + happy + error per tool) |
| Unchanged | `unittests/test_smoke.py` | Import smoke test (keep as-is) |

---

## Task 1: Worktree + project skeleton

**Files:** none created yet — just workspace setup

- [ ] **Step 1: Create worktree**

```powershell
cd C:\github\bss-mcp
git worktree add .worktrees/feature-server-and-tests -b feature/server-and-tests
cd .worktrees/feature-server-and-tests
```

- [ ] **Step 2: Verify asyncio_mode is set**

Check `pyproject.toml` contains:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["unittests"]
```
This allows `async def test_*` functions without `@pytest.mark.asyncio` decorators. It is already present in the scaffold — just confirm before writing async tests.

- [ ] **Step 3: Verify baseline tests pass**

```powershell
tox -e tests
```

Expected: `1 passed` (the smoke test).

- [ ] **Step 4: Create stub files so mypy doesn't error on missing modules**

Create `src/bss_mcp/server.py` with just the module docstring (no tools yet):

```python
"""FastMCP server wrapping BssClient."""
from fastmcp import FastMCP
from bssclient.client.bssclient import BssClient


def create_server(client: BssClient) -> FastMCP:
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError
```

Create `src/bss_mcp/settings.py` with just the module docstring:

```python
"""Env-var configuration for bss-mcp."""
```

Create `unittests/conftest.py`:

```python
"""Shared fixtures and test-data builders."""
```

Create `unittests/test_server.py` with all module-level imports upfront — **import builders at module level, never inside test bodies** (fragile and non-idiomatic):

```python
"""Tests for bss_mcp.server."""
import pytest
from unittest.mock import AsyncMock
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from bssclient.client.bssclient import BssClient
from bss_mcp.server import create_server
from unittests.conftest import build_aufgabe_stats, build_ermittlungsauftrag
```

- [ ] **Step 5: Run mypy to ensure stubs are type-clean**

```powershell
tox -e type_check
```

Expected: no errors (stubs are nearly empty).

---

## Task 2: Tool-list test → register all four tool stubs

**Files:** `unittests/conftest.py`, `unittests/test_server.py`, `src/bss_mcp/server.py`

### Step 2a: Write conftest fixtures

- [ ] **Step 1: Write the conftest.py fixtures**

Replace `unittests/conftest.py` with:

```python
"""Shared fixtures and test-data builders."""
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from bssclient.client.bssclient import BssClient
from bssclient.models.aufgabe import AufgabeStats
from bssclient.models.ermittlungsauftrag import Ermittlungsauftrag
from bss_mcp.server import create_server


@pytest.fixture
def mock_bss_client() -> AsyncMock:
    return AsyncMock(spec=BssClient)


@pytest.fixture
def bss_server(mock_bss_client: AsyncMock) -> FastMCP:
    return create_server(mock_bss_client)


def build_prozess_dict() -> dict:
    return {
        "id": str(uuid4()),
        "status": "Offen",
        "statusText": "Offen",
        "typ": "Ermittlungsauftrag",
        "ausloeser": "Test",
        "externeId": "TEST-001",
        "ausloeserDaten": "{}",
    }


def build_ermittlungsauftrag() -> Ermittlungsauftrag:
    return Ermittlungsauftrag.model_validate(
        {
            "id": str(uuid4()),
            "vertragId": str(uuid4()),
            "lieferbeginn": "2024-01-01T00:00:00+00:00",
            "lieferende": None,
            "notizen": [],
            "kategorie": "Ermittlungsauftrag",
            "prozess": build_prozess_dict(),
        }
    )


def build_aufgabe_stats() -> AufgabeStats:
    return AufgabeStats(stats={})
```

### Step 2b: Write the tool-list test (TDD — will fail)

- [ ] **Step 2: Add tool-list test to test_server.py**

Append to `unittests/test_server.py`:

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

- [ ] **Step 3: Run test — expect failure**

```powershell
tox -e tests -- -v unittests/test_server.py::test_server_exposes_expected_tools
```

Expected: FAIL — `create_server` raises `NotImplementedError`.

### Step 2c: Implement create_server with all four stubs

- [ ] **Step 4: Implement all four tool stubs in server.py**

Replace `src/bss_mcp/server.py` with:

```python
"""FastMCP server wrapping BssClient."""
from fastmcp import FastMCP
from bssclient.client.bssclient import BssClient
from bssclient.models.aufgabe import AufgabeStats
from bssclient.models.ermittlungsauftrag import Ermittlungsauftrag


def create_server(client: BssClient) -> FastMCP:
    mcp = FastMCP("bss-mcp")

    @mcp.tool
    async def get_ermittlungsauftraege(
        limit: int = 0, offset: int = 0
    ) -> list[Ermittlungsauftrag]:
        raise NotImplementedError

    @mcp.tool
    async def get_ermittlungsauftraege_by_malo(malo_id: str) -> list[Ermittlungsauftrag]:
        raise NotImplementedError

    @mcp.tool
    async def get_aufgabe_stats() -> AufgabeStats:
        raise NotImplementedError

    @mcp.tool
    async def get_all_ermittlungsauftraege(package_size: int = 100) -> list[Ermittlungsauftrag]:
        raise NotImplementedError

    return mcp


def main() -> None:
    raise NotImplementedError
```

- [ ] **Step 5: Run tool-list test — expect pass**

```powershell
tox -e tests -- -v unittests/test_server.py::test_server_exposes_expected_tools
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/bss_mcp/server.py unittests/conftest.py unittests/test_server.py src/bss_mcp/settings.py
git commit -m "test: add tool-list test and four stub tools in create_server"
```

---

## Task 3: `get_ermittlungsauftraege` — happy path + error path

**Files:** `unittests/test_server.py`, `src/bss_mcp/server.py`

- [ ] **Step 1: Write the two tests**

Append to `unittests/test_server.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```powershell
tox -e tests -- -v unittests/test_server.py -k "ermittlungsauftraege and not malo"
```

Expected: FAIL — tool raises `NotImplementedError`.

- [ ] **Step 3: Implement the tool**

In `src/bss_mcp/server.py`, replace the stub body:

```python
    @mcp.tool
    async def get_ermittlungsauftraege(
        limit: int = 0, offset: int = 0
    ) -> list[Ermittlungsauftrag]:
        return await client.get_ermittlungsauftraege(limit=limit, offset=offset)
```

- [ ] **Step 4: Run tests — expect pass**

```powershell
tox -e tests -- -v unittests/test_server.py -k "ermittlungsauftraege and not malo"
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/bss_mcp/server.py unittests/test_server.py
git commit -m "feat: implement get_ermittlungsauftraege tool with tests"
```

---

## Task 4: `get_ermittlungsauftraege_by_malo` — happy path + error path

**Files:** `unittests/test_server.py`, `src/bss_mcp/server.py`

- [ ] **Step 1: Write the two tests**

Append to `unittests/test_server.py`:

```python
async def test_get_ermittlungsauftraege_by_malo_returns_list(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    ea = build_ermittlungsauftrag()
    mock_bss_client.get_ermittlungsauftraege_by_malo.return_value = [ea]
    async with Client(bss_server) as client:
        result = await client.call_tool(
            "get_ermittlungsauftraege_by_malo", {"malo_id": "DE0001234567890"}
        )
    assert result.data is not None
    assert len(result.data) == 1
    mock_bss_client.get_ermittlungsauftraege_by_malo.assert_awaited_once_with(
        malo_id="DE0001234567890"
    )


async def test_get_ermittlungsauftraege_by_malo_propagates_error(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_ermittlungsauftraege_by_malo.side_effect = Exception("not found")
    async with Client(bss_server) as client:
        with pytest.raises(ToolError, match="not found"):
            await client.call_tool(
                "get_ermittlungsauftraege_by_malo", {"malo_id": "DE0001234567890"}
            )
```

- [ ] **Step 2: Run tests — expect failure**

```powershell
tox -e tests -- -v unittests/test_server.py -k "by_malo"
```

Expected: FAIL.

- [ ] **Step 3: Implement the tool**

```python
    @mcp.tool
    async def get_ermittlungsauftraege_by_malo(malo_id: str) -> list[Ermittlungsauftrag]:
        return await client.get_ermittlungsauftraege_by_malo(malo_id=malo_id)
```

- [ ] **Step 4: Run tests — expect pass**

```powershell
tox -e tests -- -v unittests/test_server.py -k "by_malo"
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/bss_mcp/server.py unittests/test_server.py
git commit -m "feat: implement get_ermittlungsauftraege_by_malo tool with tests"
```

---

## Task 5: `get_aufgabe_stats` — happy path + error path

**Files:** `unittests/test_server.py`, `src/bss_mcp/server.py`

- [ ] **Step 1: Write the two tests**

Append to `unittests/test_server.py`:

```python
async def test_get_aufgabe_stats_returns_stats(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    stats = build_aufgabe_stats()
    mock_bss_client.get_aufgabe_stats.return_value = stats
    async with Client(bss_server) as client:
        result = await client.call_tool("get_aufgabe_stats", {})
    assert result.data is not None
    mock_bss_client.get_aufgabe_stats.assert_awaited_once_with()


async def test_get_aufgabe_stats_propagates_error(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_aufgabe_stats.side_effect = Exception("stats unavailable")
    async with Client(bss_server) as client:
        with pytest.raises(ToolError, match="stats unavailable"):
            await client.call_tool("get_aufgabe_stats", {})
```

- [ ] **Step 2: Run tests — expect failure**

```powershell
tox -e tests -- -v unittests/test_server.py -k "aufgabe_stats"
```

Expected: FAIL.

- [ ] **Step 3: Implement the tool**

```python
    @mcp.tool
    async def get_aufgabe_stats() -> AufgabeStats:
        return await client.get_aufgabe_stats()
```

- [ ] **Step 4: Run tests — expect pass**

```powershell
tox -e tests -- -v unittests/test_server.py -k "aufgabe_stats"
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/bss_mcp/server.py unittests/test_server.py
git commit -m "feat: implement get_aufgabe_stats tool with tests"
```

---

## Task 6: `get_all_ermittlungsauftraege` — happy path + error path

**Files:** `unittests/test_server.py`, `src/bss_mcp/server.py`

- [ ] **Step 1: Write the two tests**

Append to `unittests/test_server.py`:

```python
async def test_get_all_ermittlungsauftraege_passes_package_size(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_all_ermittlungsauftraege.return_value = []
    async with Client(bss_server) as client:
        result = await client.call_tool(
            "get_all_ermittlungsauftraege", {"package_size": 50}
        )
    assert result.data is not None
    # Verifies delegation only — pagination logic lives in bssclient, not here.
    mock_bss_client.get_all_ermittlungsauftraege.assert_awaited_once_with(package_size=50)


async def test_get_all_ermittlungsauftraege_default_package_size(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_all_ermittlungsauftraege.return_value = []
    async with Client(bss_server) as client:
        result = await client.call_tool("get_all_ermittlungsauftraege", {})
    assert result.data is not None
    mock_bss_client.get_all_ermittlungsauftraege.assert_awaited_once_with(package_size=100)


async def test_get_all_ermittlungsauftraege_propagates_error(
    bss_server: FastMCP, mock_bss_client: AsyncMock
) -> None:
    mock_bss_client.get_all_ermittlungsauftraege.side_effect = Exception("timeout")
    async with Client(bss_server) as client:
        with pytest.raises(ToolError, match="timeout"):
            await client.call_tool("get_all_ermittlungsauftraege", {})
```

- [ ] **Step 2: Run tests — expect failure**

```powershell
tox -e tests -- -v unittests/test_server.py -k "get_all"
```

Expected: FAIL.

- [ ] **Step 3: Implement the tool**

```python
    @mcp.tool
    async def get_all_ermittlungsauftraege(package_size: int = 100) -> list[Ermittlungsauftrag]:
        return await client.get_all_ermittlungsauftraege(package_size=package_size)
```

- [ ] **Step 4: Run tests — expect pass**

```powershell
tox -e tests -- -v unittests/test_server.py -k "get_all"
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/bss_mcp/server.py unittests/test_server.py
git commit -m "feat: implement get_all_ermittlungsauftraege tool with tests"
```

---

## Task 7: settings.py + main()

No TDD for settings.py — it reads env vars and calls bssclient constructors that hit the network. Integration-tested by running the server manually. `main()` is tested implicitly: if it type-checks and the server starts, it works.

**Files:** `src/bss_mcp/settings.py`, `src/bss_mcp/server.py`

- [ ] **Step 1: Implement settings.py**

```python
"""Env-var configuration for bss-mcp."""
from enum import StrEnum

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

from bssclient.client.bssclient import BasicAuthBssClient, BssClient, OAuthBssClient
from bssclient.client.config import BasicAuthBssConfig, OAuthBssConfig


class AuthType(StrEnum):
    BASIC = "basic"
    OAUTH = "oauth"


class BssMcpSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BSS_", env_file=".env", extra="ignore")

    url: HttpUrl
    auth_type: AuthType = AuthType.BASIC
    user: str = ""
    password: str = ""
    client_id: str = ""
    client_secret: str = ""
    token_url: HttpUrl | None = None

    def create_client(self) -> BssClient:
        server_url = URL(str(self.url))
        if self.auth_type == AuthType.OAUTH:
            return OAuthBssClient(
                OAuthBssConfig(
                    server_url=server_url,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    token_url=self.token_url,  # type: ignore[arg-type]
                )
            )
        return BasicAuthBssClient(
            BasicAuthBssConfig(server_url=server_url, usr=self.user, pwd=self.password)
        )
```

**Env vars read by settings (document in `.env.example`):**

| Variable | Required | Default | Example |
|---|---|---|---|
| `BSS_URL` | Yes | — | `https://basicsupply.example.de/` |
| `BSS_AUTH_TYPE` | No | `basic` | `oauth` |
| `BSS_USER` | If basic auth | `""` | `admin` |
| `BSS_PASSWORD` | If basic auth | `""` | `secret` |
| `BSS_CLIENT_ID` | If OAuth | `""` | `my-client` |
| `BSS_CLIENT_SECRET` | If OAuth | `""` | `my-secret` |
| `BSS_TOKEN_URL` | If OAuth | `None` | `https://auth.example.de/oauth2/token` |

- [ ] **Step 2: Implement main() in server.py**

Replace `main()` in `src/bss_mcp/server.py`:

```python
def main() -> None:
    from bss_mcp.settings import BssMcpSettings

    settings = BssMcpSettings()
    client = settings.create_client()
    mcp = create_server(client)
    mcp.run()
```

The import is deferred so `create_server` stays importable in tests without triggering env-var reads.

- [ ] **Step 3: Run full tox type_check**

```powershell
tox -e type_check
```

Fix any mypy errors before committing. Common issues:
- `HttpUrl | None` passed where `HttpUrl` required → add `assert self.token_url is not None` before the OAuth config construction
- `StrEnum` — available from Python 3.11, no backport needed

- [ ] **Step 4: Commit**

```powershell
git add src/bss_mcp/settings.py src/bss_mcp/server.py
git commit -m "feat: add settings.py and wire main() entry point"
```

---

## Task 8: Full tox run + coverage gate

- [ ] **Step 1: Run all tox environments**

```powershell
tox
```

Expected: `tests`, `linting`, `coverage`, `type_check` all green.

If `coverage` reports under 80%, investigate which lines are uncovered and add tests or mark them `# pragma: no cover` (acceptable for `main()` and the deferred import).

- [ ] **Step 2: If linting fails**

`pylint` may warn about the nested function pattern inside `create_server`. Add to the function:
```python
# pylint: disable=function-redefined
```
Or suppress at module level — follow existing patterns in the repo.

- [ ] **Step 3: Push and open PR**

```powershell
git push -u origin feature/server-and-tests
gh pr create --title "feat: implement MCP server and full test suite" --body "$(cat <<'EOF'
## Summary
- Adds `create_server(client: BssClient) -> FastMCP` with four read-only tools
- Adds `settings.py` reading BSS_URL/BSS_AUTH_TYPE/BSS_USER/... env vars
- Full test suite: tool-list + 2-3 tests per tool using FastMCP in-process Client
- All tools strictly typed — no dict/Any in tool interfaces (per CLAUDE.md)

## Test plan
- [ ] `tox -e tests` passes (smoke + server tests)
- [ ] `tox -e type_check` passes (mypy strict)
- [ ] `tox -e linting` passes
- [ ] `tox -e coverage` ≥ 80%

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Poll CI until green**

```powershell
gh pr checks --repo Hochfrequenz/bss-mcp
```

---

## Final server.py (complete reference)

```python
"""FastMCP server wrapping BssClient."""
from fastmcp import FastMCP
from bssclient.client.bssclient import BssClient
from bssclient.models.aufgabe import AufgabeStats
from bssclient.models.ermittlungsauftrag import Ermittlungsauftrag


def create_server(client: BssClient) -> FastMCP:
    mcp = FastMCP("bss-mcp")

    @mcp.tool
    async def get_ermittlungsauftraege(
        limit: int = 0, offset: int = 0
    ) -> list[Ermittlungsauftrag]:
        return await client.get_ermittlungsauftraege(limit=limit, offset=offset)

    @mcp.tool
    async def get_ermittlungsauftraege_by_malo(malo_id: str) -> list[Ermittlungsauftrag]:
        return await client.get_ermittlungsauftraege_by_malo(malo_id=malo_id)

    @mcp.tool
    async def get_aufgabe_stats() -> AufgabeStats:
        return await client.get_aufgabe_stats()

    @mcp.tool
    async def get_all_ermittlungsauftraege(package_size: int = 100) -> list[Ermittlungsauftrag]:
        return await client.get_all_ermittlungsauftraege(package_size=package_size)

    return mcp


def main() -> None:
    from bss_mcp.settings import BssMcpSettings

    settings = BssMcpSettings()
    client = settings.create_client()
    mcp = create_server(client)
    mcp.run()
```
