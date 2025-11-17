import logging
from typing import TYPE_CHECKING, Any, cast

import obstore
import restate
import workstate
import workstate.obstore
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .restate_yt_dlp import Downloader, create_service

if TYPE_CHECKING:
    from yt_dlp import _Params


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")  # pyright: ignore[reportUnannotatedClassAttribute]

    service_name: str = "YoutubeDownloader"
    object_store_url: str
    obstore_allow_http: bool = False
    ytdlp_defaults: dict[str, Any] | None = None
    ytdlp_overrides: dict[str, Any] | None = None
    identity_keys: list[str] = Field(alias="restate_identity_keys", default=[])


settings = Settings()  # pyright: ignore[reportCallIssue]

store = obstore.store.from_url(
    settings.object_store_url,
    client_options={"allow_http": settings.obstore_allow_http},
)
state = workstate.obstore.StateManager(store)

logging.basicConfig(level=logging.INFO)

downloader = Downloader(
    state,
    cast("_Params", settings.ytdlp_defaults),
)

service = create_service(downloader, service_name=settings.service_name)

app = restate.app(services=[service], identity_keys=settings.identity_keys)
