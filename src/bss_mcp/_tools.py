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
