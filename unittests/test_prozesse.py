import uuid
from unittest.mock import AsyncMock, MagicMock, patch


async def test_list_prozesse_for_malo_returns_raw_json():
    malo_id = "12345678901"
    expected = [{"id": str(uuid.uuid4()), "status": "InBearbeitung", "marktlokationsId": malo_id}]

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = expected

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get.return_value = mock_response

    with patch("bss_mcp._tools.BssMcpSettings") as mock_settings_cls:
        s = mock_settings_cls.return_value
        s.url = "https://bss.example.com"
        s.auth_type = MagicMock()
        s.auth_type.value = "basic"
        s.user = "u"
        s.password = "p"

        with patch("bss_mcp._tools.httpx.AsyncClient", return_value=mock_client):
            from bss_mcp._tools import list_prozesse_for_malo
            result = await list_prozesse_for_malo(malo_id)

    assert result == expected
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert malo_id in str(call_args)


async def test_get_prozess_by_id_returns_raw_json():
    prozess_id = str(uuid.uuid4())
    expected = {"id": prozess_id, "status": "Abgeschlossen"}

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = expected

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get.return_value = mock_response

    with patch("bss_mcp._tools.BssMcpSettings") as mock_settings_cls:
        s = mock_settings_cls.return_value
        s.url = "https://bss.example.com"
        s.auth_type = MagicMock()
        s.auth_type.value = "basic"
        s.user = "u"
        s.password = "p"

        with patch("bss_mcp._tools.httpx.AsyncClient", return_value=mock_client):
            from bss_mcp._tools import get_prozess_by_id
            result = await get_prozess_by_id(prozess_id)

    assert result == expected
    call_url = mock_client.get.call_args[0][0]
    assert prozess_id in call_url
