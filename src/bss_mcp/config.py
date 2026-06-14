from enum import Enum
from yarl import URL
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from bssclient.client.bssclient import BasicAuthBssClient, BssClient, OAuthBssClient
from bssclient.client.config import BasicAuthBssConfig, OAuthBssConfig


class AuthType(str, Enum):
    BASIC = "basic"
    OAUTH = "oauth"


class BssMcpSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BSS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url: AnyHttpUrl
    auth_type: AuthType = AuthType.BASIC
    user: str | None = None
    password: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    token_url: AnyHttpUrl | None = None


def get_bss_client(settings: BssMcpSettings) -> BssClient:
    server_url = URL(str(settings.url))
    if settings.auth_type == AuthType.BASIC:
        if not settings.user or not settings.password:
            raise ValueError("BSS_USER and BSS_PASSWORD required for basic auth")
        return BasicAuthBssClient(
            BasicAuthBssConfig(server_url=server_url, usr=settings.user, pwd=settings.password)
        )
    if not settings.client_id or not settings.client_secret or not settings.token_url:
        raise ValueError("BSS_CLIENT_ID, BSS_CLIENT_SECRET, BSS_TOKEN_URL required for OAuth")
    return OAuthBssClient(
        OAuthBssConfig(
            server_url=server_url,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            token_url=str(settings.token_url),
        )
    )
