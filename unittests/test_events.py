import uuid
from unittest.mock import AsyncMock, MagicMock, patch


async def test_get_events_for_prozess_calls_client_with_correct_type():
    from bssclient.models.events import EventHeader

    prozess_id = str(uuid.uuid4())
    mock_event = MagicMock(spec=EventHeader)
    mock_event.model_dump.return_value = {"eventNumber": 1, "eventType": "ProzessGestartet"}

    mock_client = AsyncMock()
    mock_client.get_events.return_value = [mock_event]

    with patch("bss_mcp._tools.get_bss_client", return_value=mock_client):
        with patch("bss_mcp._tools.BssMcpSettings"):
            from bss_mcp._tools import get_events_for_prozess
            result = await get_events_for_prozess(prozess_id)

    mock_client.get_events.assert_called_once_with("Prozess", uuid.UUID(prozess_id))
    assert result == [{"eventNumber": 1, "eventType": "ProzessGestartet"}]
    mock_client.close_session.assert_called_once()


async def test_get_events_for_aufgabe_calls_client_with_correct_type():
    from bssclient.models.events import EventHeader

    aufgabe_id = str(uuid.uuid4())
    mock_event = MagicMock(spec=EventHeader)
    mock_event.model_dump.return_value = {"eventNumber": 1, "eventType": "AufgabeErstellt"}

    mock_client = AsyncMock()
    mock_client.get_events.return_value = [mock_event]

    with patch("bss_mcp._tools.get_bss_client", return_value=mock_client):
        with patch("bss_mcp._tools.BssMcpSettings"):
            from bss_mcp._tools import get_events_for_aufgabe
            result = await get_events_for_aufgabe(aufgabe_id)

    mock_client.get_events.assert_called_once_with("Aufgabe", uuid.UUID(aufgabe_id))
    assert result == [{"eventNumber": 1, "eventType": "AufgabeErstellt"}]
    mock_client.close_session.assert_called_once()
