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
    raise NotImplementedError
