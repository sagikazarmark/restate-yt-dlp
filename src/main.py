from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import obstore
import pydantic_obstore
import restate
import structlog
import workstate
import workstate.obstore
from glide_sync import (
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    ServerCredentials,
)
from pydantic import BaseModel, Field, RedisDsn
from pydantic_restate import WorkerSettings
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logger import Logger
from .params import Params
from .progress import ValkeyProgressHook
from .restate_yt_dlp import Executor, create_service
from .restate_yt_dlp.executor import ProgressHook
from .restate_yt_dlp.restate import Options as RestateOptions

if TYPE_CHECKING:
    from obstore.store import ClientConfig
    from yt_dlp import _Params


class ObstoreSettings(pydantic_obstore.Config):
    url: str | None = None


class Restate(RestateOptions, WorkerSettings):
    pass


class ValkeySettings(BaseModel):
    dsn: RedisDsn = Field(description="Valkey connection string")
    request_timeout: int | None = Field(
        default=None,
        description="Valkey request timeout",
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")  # pyright: ignore[reportUnannotatedClassAttribute]

    obstore: ObstoreSettings = Field(default_factory=ObstoreSettings)

    yt_dlp_defaults: Params = {}

    valkey: ValkeySettings | None = Field(default=None, description="Valkey settings")

    restate: Restate = Field(default_factory=Restate, description="Restate settings")


settings = Settings()

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

progress_hook: ProgressHook | None = None

if settings.valkey:
    structlog.get_logger().info("Initializing valkey progress hook")

    valkey = settings.valkey

    credentials: ServerCredentials | None = None

    if valkey.dsn.username and valkey.dsn.password:
        credentials = ServerCredentials(valkey.dsn.username, valkey.dsn.password)

    database: int | None = None

    if valkey.dsn.path:
        database_candidate = valkey.dsn.path.strip("/").split("/")[0]
        if database_candidate.isdigit():
            database = int(database_candidate)

    config = GlideClientConfiguration(
        [
            NodeAddress(valkey.dsn.host, valkey.dsn.port or 6379),
        ],
        request_timeout=valkey.request_timeout,
        credentials=credentials,
        database_id=database,
    )

    client = GlideClient.create(config)

    progress_hook = ValkeyProgressHook(client)

executor = Executor(
    persister,
    defaults=cast(
        "_Params",
        settings.yt_dlp_defaults | {"logger": Logger(structlog.get_logger("yt-dlp"))},
    ),
    progress_hook=progress_hook,
    logger=structlog.get_logger("executor"),
)

service = create_service(executor, settings.restate)

app = restate.app(services=[service], identity_keys=settings.restate.identity_keys)
