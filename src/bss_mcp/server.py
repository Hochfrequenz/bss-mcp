from pathlib import Path
from fastmcp import FastMCP
from bss_mcp._tools import (
    get_aufgabe_stats,
    get_ermittlungsauftraege_for_malo,
    get_events_for_aufgabe,
    get_events_for_prozess,
    get_prozess_by_id,
    list_prozesse_for_malo,
)

mcp = FastMCP("bss-mcp")

mcp.tool()(get_ermittlungsauftraege_for_malo)
mcp.tool()(get_aufgabe_stats)
mcp.tool()(get_events_for_prozess)
mcp.tool()(get_events_for_aufgabe)
mcp.tool()(list_prozesse_for_malo)
mcp.tool()(get_prozess_by_id)


@mcp.prompt()
def bug_hunt_workflow() -> str:
    """BSS bug hunt workflow — which tool to use when and in which order."""
    return (Path(__file__).parent / "DEBUGGING.md").read_text(encoding="utf-8")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
