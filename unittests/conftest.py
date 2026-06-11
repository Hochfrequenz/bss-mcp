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
