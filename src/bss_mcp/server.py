"""FastMCP server wrapping BssClient."""
from fastmcp import FastMCP
from bssclient.client.bssclient import BssClient


def create_server(client: BssClient) -> FastMCP:
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError
