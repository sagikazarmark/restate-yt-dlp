from typing import Any

import obstore
import restate
import workstate
import workstate.obstore
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .restate_yt_dlp import Downloader, DownloaderOptions, create_service


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")  # pyright: ignore[reportUnannotatedClassAttribute]

    object_store_url: str
    obstore_allow_http: bool = False
    youtube_params: dict[str, Any] | None = None  # pyright: ignore[reportExplicitAny]
    options: DownloaderOptions = DownloaderOptions()
    identity_keys: list[str] = Field(alias="restate_identity_keys", default=[])


settings = Settings()  # pyright: ignore[reportCallIssue]

store = obstore.store.from_url(
    settings.object_store_url,
    client_options={"allow_http": settings.obstore_allow_http},
)
state = workstate.obstore.StateManager(store)

downloader = Downloader(
    state,
    settings.youtube_params,  # pyright: ignore[reportArgumentType]
    settings.options,
)

service = create_service(downloader)

app = restate.app(services=[service], identity_keys=settings.identity_keys)
