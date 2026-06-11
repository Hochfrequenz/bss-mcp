import os
from unittest.mock import patch


def test_get_bss_client_returns_basic_auth_client():
    env = {
        "BSS_URL": "https://bss.example.com",
        "BSS_AUTH_TYPE": "basic",
        "BSS_USER": "user",
        "BSS_PASSWORD": "pass",
    }
    with patch.dict(os.environ, env, clear=True):
        from bss_mcp.config import BssMcpSettings, get_bss_client
        from bssclient.client.bssclient import BasicAuthBssClient
        client = get_bss_client(BssMcpSettings())
        assert isinstance(client, BasicAuthBssClient)


def test_get_bss_client_returns_oauth_client():
    env = {
        "BSS_URL": "https://bss.example.com",
        "BSS_AUTH_TYPE": "oauth",
        "BSS_CLIENT_ID": "cid",
        "BSS_CLIENT_SECRET": "secret",
        "BSS_TOKEN_URL": "https://auth.example.com/token",
    }
    with patch.dict(os.environ, env, clear=True):
        from bss_mcp.config import BssMcpSettings, get_bss_client
        from bssclient.client.bssclient import OAuthBssClient
        client = get_bss_client(BssMcpSettings())
        assert isinstance(client, OAuthBssClient)
