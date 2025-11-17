import logging
from typing import Any

import obstore
import restate
import workstate
import workstate.obstore
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .restate_yt_dlp import Downloader, create_service


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")  # pyright: ignore[reportUnannotatedClassAttribute]

    service_name: str = "YoutubeDownloader"
    object_store_url: str
    obstore_allow_http: bool = False
    youtube_params: dict[str, Any] | None = None  # pyright: ignore[reportExplicitAny]
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
    settings.youtube_params,  # pyright: ignore[reportArgumentType]
)

service = create_service(downloader, service_name=settings.service_name)

app = restate.app(services=[service], identity_keys=settings.identity_keys)
