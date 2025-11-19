import logging
from typing import TYPE_CHECKING, Any, cast

import obstore
import pydantic_obstore
import restate
import workstate
import workstate.obstore
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .restate_yt_dlp import Downloader, create_service

if TYPE_CHECKING:
    from obstore.store import ClientConfig
    from yt_dlp import _Params


class ObstoreSettings(pydantic_obstore.Config):
    url: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")  # pyright: ignore[reportUnannotatedClassAttribute]

    service_name: str = "yt-dlp"

    obstore: ObstoreSettings

    yt_dlp_defaults: dict[str, Any] | None = None

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
    defaults=cast("_Params", settings.yt_dlp_defaults),
)

service = create_service(downloader, service_name=settings.service_name)

app = restate.app(services=[service], identity_keys=settings.identity_keys)
