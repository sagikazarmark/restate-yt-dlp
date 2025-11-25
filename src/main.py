from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

import obstore
import pydantic_obstore
import restate
import structlog
import workstate
import workstate.obstore
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logger import Logger
from .restate_yt_dlp import Executor, create_service

if TYPE_CHECKING:
    from obstore.store import ClientConfig
    from yt_dlp import _Params


class ObstoreSettings(pydantic_obstore.Config):
    url: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")  # pyright: ignore[reportUnannotatedClassAttribute]

    obstore: ObstoreSettings = Field(default_factory=ObstoreSettings)

    yt_dlp_defaults: dict[str, Any] | None = None

    service_name: str = "yt-dlp"

    identity_keys: list[str] = Field(alias="restate_identity_keys", default=[])


settings = Settings()  # pyright: ignore[reportCallIssue]

# logging.basicConfig(level=logging.INFO)
structlog.stdlib.recreate_defaults(log_level=logging.INFO)

store: obstore.store.ObjectStore | None = None
client_options: ClientConfig | None = None

if settings.obstore.client_options:
    client_options = cast(
        "ClientConfig",
        settings.obstore.client_options.model_dump(exclude_none=True),
    )

if settings.obstore.url:
    store = obstore.store.from_url(settings.obstore.url, client_options=client_options)

persister = workstate.obstore.DirectoryPersister(
    store,
    client_options=client_options,
    logger=structlog.get_logger("workstate"),
)

executor = Executor(
    persister,
    defaults=cast(
        "_Params",
        (settings.yt_dlp_defaults or {})
        | {"logger": Logger(structlog.get_logger("yt-dlp"))},
    ),
    logger=structlog.get_logger("executor"),
)

service = create_service(executor, service_name=settings.service_name)

app = restate.app(services=[service], identity_keys=settings.identity_keys)
