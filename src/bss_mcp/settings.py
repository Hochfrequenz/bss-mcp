"""Env-var configuration for bss-mcp."""
from enum import StrEnum

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

from bssclient.client.bssclient import BasicAuthBssClient, BssClient, OAuthBssClient
from bssclient.client.config import BasicAuthBssConfig, OAuthBssConfig


class AuthType(StrEnum):
    """Authentication type supported by the BSS server."""

    BASIC = "basic"
    OAUTH = "oauth"


class BssMcpSettings(BaseSettings):
    """Pydantic-settings model reading BSS_* environment variables."""

    model_config = SettingsConfigDict(env_prefix="BSS_", env_file=".env", extra="ignore")

    url: HttpUrl
    auth_type: AuthType = AuthType.BASIC
    user: str = ""
    password: str = ""
    client_id: str = ""
    client_secret: str = ""
    token_url: HttpUrl | None = None

    def create_client(self) -> BssClient:
        """Instantiate the appropriate BssClient based on the configured auth type."""
        server_url = URL(str(self.url))
        if self.auth_type == AuthType.OAUTH:
            if self.token_url is None:
                raise ValueError("BSS_TOKEN_URL is required when BSS_AUTH_TYPE=oauth")
            return OAuthBssClient(
                OAuthBssConfig(
                    server_url=server_url,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    token_url=self.token_url,
                )
            )
        return BasicAuthBssClient(
            BasicAuthBssConfig(server_url=server_url, usr=self.user, pwd=self.password)
        )
