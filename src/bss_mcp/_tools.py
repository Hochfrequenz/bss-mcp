"""Pure async tool functions. No FastMCP imports — directly testable."""
# httpx and AuthType used in Task 5 (Prozess tools) — imported here to keep imports at top
import httpx
import uuid as _uuid

from bss_mcp.config import AuthType, BssMcpSettings, get_bss_client


async def get_ermittlungsauftraege_for_malo(malo_id: str) -> list[dict]:
    """
    Find all Ermittlungsaufträge in BSS for a given MaLo-ID.
    Returns empty list if no orders exist. BSS indexes these by MaLo only — no MeLo lookup.
    Use this first when investigating wrong customer data or missing handover processes.
    """
    settings = BssMcpSettings()
    client = get_bss_client(settings)
    try:
        results = await client.get_ermittlungsauftraege_by_malo(malo_id)
        return [r.model_dump(mode="json") for r in results]
    finally:
        await client.close_session()


async def get_aufgabe_stats() -> dict:
    """
    Get aggregate counts for all Aufgabe types in BSS (Ermittlungsauftrag etc.).
    Use to check if the backlog is unexpectedly high or to confirm BSS is processing normally.
    """
    settings = BssMcpSettings()
    client = get_bss_client(settings)
    try:
        result = await client.get_aufgabe_stats()
        return result.model_dump(mode="json")
    finally:
        await client.close_session()


async def get_events_for_prozess(prozess_id: str) -> list[dict]:
    """
    Get event history for a BSS Prozess by UUID.
    Returns EventHeaders in order. Gaps in sequence indicate deserialization issues — escalate to team.
    Use after list_prozesse_for_malo to trace what happened to a stuck or failed process.
    """
    settings = BssMcpSettings()
    client = get_bss_client(settings)
    try:
        results = await client.get_events("Prozess", _uuid.UUID(prozess_id))
        return [r.model_dump(mode="json") for r in results]
    finally:
        await client.close_session()


async def get_events_for_aufgabe(aufgabe_id: str) -> list[dict]:
    """
    Get event history for a BSS Aufgabe by UUID.
    Returns EventHeaders in order. Use to trace the lifecycle of an Ermittlungsauftrag.
    """
    settings = BssMcpSettings()
    client = get_bss_client(settings)
    try:
        results = await client.get_events("Aufgabe", _uuid.UUID(aufgabe_id))
        return [r.model_dump(mode="json") for r in results]
    finally:
        await client.close_session()


def _httpx_auth(settings: BssMcpSettings) -> tuple[str, str]:
    """BasicAuth tuple for httpx. OAuth not yet supported for raw Prozess endpoints."""
    if settings.auth_type.value == "basic":
        if not settings.user or not settings.password:
            raise ValueError("BSS_USER and BSS_PASSWORD required for basic auth")
        return (settings.user, settings.password)
    raise NotImplementedError(
        "OAuth not yet supported for Prozess endpoints. Use BasicAuth or contribute OAuth support."
    )


async def list_prozesse_for_malo(malo_id: str) -> list[dict]:
    """
    List all Prozesse in BSS for a given MaLo-ID.
    Returns current state of each process. Use to find stuck, unexpected, or missing processes.
    NOTE: Endpoint path unverified — check Swagger before first use (no .env present during authoring).
    """
    settings = BssMcpSettings()
    bss_url = str(settings.url).rstrip("/")
    # VERIFY: path /api/Prozess/find is a best-guess approximation — check {BSS_URL}/swagger/index.html:
    url = f"{bss_url}/api/Prozess/find"
    params = {"marktlokationId": malo_id}
    async with httpx.AsyncClient(auth=_httpx_auth(settings)) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def get_prozess_by_id(prozess_id: str) -> dict:
    """
    Get a single Prozess from BSS by UUID.
    Returns full process state: status, timestamps, MaLo/MeLo reference.
    Use after list_prozesse_for_malo to inspect a specific process in detail.
    NOTE: Endpoint path unverified — check Swagger before first use (no .env present during authoring).
    """
    settings = BssMcpSettings()
    bss_url = str(settings.url).rstrip("/")
    # VERIFY: path /api/Prozess/{id} is a best-guess approximation — check {BSS_URL}/swagger/index.html:
    url = f"{bss_url}/api/Prozess/{prozess_id}"
    async with httpx.AsyncClient(auth=_httpx_auth(settings)) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
