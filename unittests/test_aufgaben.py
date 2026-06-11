from unittest.mock import AsyncMock, MagicMock, patch


async def test_get_ermittlungsauftraege_for_malo_calls_client_and_returns_list():
    from bssclient.models.ermittlungsauftrag import Ermittlungsauftrag

    mock_ea = MagicMock(spec=Ermittlungsauftrag)
    mock_ea.model_dump.return_value = {"id": "abc", "marktlokationsId": "12345678901"}

    mock_client = AsyncMock()
    mock_client.get_ermittlungsauftraege_by_malo.return_value = [mock_ea]

    with patch("bss_mcp._tools.get_bss_client", return_value=mock_client):
        with patch("bss_mcp._tools.BssMcpSettings"):
            from bss_mcp._tools import get_ermittlungsauftraege_for_malo
            result = await get_ermittlungsauftraege_for_malo("12345678901")

    assert result == [{"id": "abc", "marktlokationsId": "12345678901"}]
    mock_client.get_ermittlungsauftraege_by_malo.assert_called_once_with("12345678901")
    mock_client.close_session.assert_called_once()


async def test_get_aufgabe_stats_returns_dict():
    from bssclient.models.aufgabe import AufgabeStats

    mock_stats = MagicMock(spec=AufgabeStats)
    mock_stats.model_dump.return_value = {"Ermittlungsauftrag": 42}

    mock_client = AsyncMock()
    mock_client.get_aufgabe_stats.return_value = mock_stats

    with patch("bss_mcp._tools.get_bss_client", return_value=mock_client):
        with patch("bss_mcp._tools.BssMcpSettings"):
            from bss_mcp._tools import get_aufgabe_stats
            result = await get_aufgabe_stats()

    assert result == {"Ermittlungsauftrag": 42}
    mock_client.close_session.assert_called_once()
