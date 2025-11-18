import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Dict, cast

import obstore
import restate
import workstate
import workstate.obstore
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .restate_yt_dlp import Downloader, create_service

if TYPE_CHECKING:
    from obstore.store import ClientConfig
    from yt_dlp import _Params


class ObstoreClientConfig(BaseModel):
    """
    HTTP client configuration for Obstore.

    See https://developmentseed.org/obstore/latest/api/store/config/#obstore.store.ClientConfig
    """

    allow_http: bool | None = Field(
        default=None,
        description="Allow non-TLS, i.e. non-HTTPS connections.",
    )

    allow_invalid_certificates: bool | None = Field(
        default=None,
        description="Skip certificate validation on https connections.",
    )

    connect_timeout: str | timedelta | None = Field(
        default=None,
        description="Timeout for only the connect phase of a Client",
    )

    default_content_type: str | None = Field(
        default=None,
        description="Default `CONTENT_TYPE` for uploads",
    )

    default_headers: Dict[str, str] | Dict[str, bytes] | None = Field(
        default=None,
        description="Default headers to be sent with each request",
    )

    http1_only: bool | None = Field(
        default=None,
        description="Only use http1 connections.",
    )

    http2_keep_alive_interval: str | None = Field(
        default=None,
        description="Interval for HTTP2 Ping frames should be sent to keep a connection alive.",
    )

    http2_keep_alive_timeout: str | timedelta | None = Field(
        default=None,
        description="Timeout for receiving an acknowledgement of the keep-alive ping.",
    )

    http2_keep_alive_while_idle: str | None = Field(
        default=None,
        description="Enable HTTP2 keep alive pings for idle connections",
    )

    http2_only: bool | None = Field(
        default=None,
        description="Only use http2 connections",
    )

    pool_idle_timeout: str | timedelta | None = Field(
        default=None,
        description=(
            "The pool max idle timeout."
            "This is the length of time an idle connection will be kept alive."
        ),
    )

    pool_max_idle_per_host: str | None = Field(
        default=None,
        description="Maximum number of idle connections per host.",
    )

    proxy_url: str | None = Field(
        default=None,
        description="HTTP proxy to use for requests.",
    )

    timeout: str | timedelta | None = Field(
        default=None,
        description=(
            "Request timeout."
            "The timeout is applied from when the request starts connecting until the "
            "response body has finished."
        ),
    )

    user_agent: str | None = Field(
        default=None,
        description="User-Agent header to be used by this client.",
    )


class ObstoreSettings(BaseModel):
    url: str

    client_options: ObstoreClientConfig | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")  # pyright: ignore[reportUnannotatedClassAttribute]

    service_name: str = "YoutubeDownloader"

    obstore: ObstoreSettings

    ytdlp_defaults: dict[str, Any] | None = None

    identity_keys: list[str] = Field(alias="restate_identity_keys", default=[])


settings = Settings()  # pyright: ignore[reportCallIssue]

store = obstore.store.from_url(
    settings.obstore.url,
    client_options=cast(
        "ClientConfig | None",
        (
            settings.obstore.client_options.model_dump(exclude_none=True)
            if settings.obstore.client_options
            else None
        ),
    ),
)
state = workstate.obstore.StateManager(store)

logging.basicConfig(level=logging.INFO)

downloader = Downloader(
    state,
    defaults=cast("_Params", settings.ytdlp_defaults),
)

service = create_service(downloader, service_name=settings.service_name)

app = restate.app(services=[service], identity_keys=settings.identity_keys)
