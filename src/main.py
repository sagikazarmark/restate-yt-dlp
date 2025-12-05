from __future__ import annotations

import json
import logging
from hashlib import sha256
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
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logger import Logger
from .params import Params
from .restate_yt_dlp import Executor, Progress, ServiceOptions, create_service
from .restate_yt_dlp.executor import ProgressHook

if TYPE_CHECKING:
    from obstore.store import ClientConfig
    from yt_dlp import _Params


class ObstoreSettings(pydantic_obstore.Config):
    url: str | None = None


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

    restate_service: ServiceOptions = Field(
        default_factory=ServiceOptions,
        description="Restate service options",
    )

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

    def valkey_progress_hook(id: str, url: str, progress: Progress):
        url_hash = sha256(url.encode()).hexdigest()

        fields = [
            "status",
            "downloaded_bytes",
            "total_bytes",
            "total_bytes_estimate",
            "elapsed",
            "eta",
            "speed",
            "_percent_str",
            "_speed_str",
            "_eta_str",
            "_total_bytes_str",
            "_total_bytes_estimate_str",
            "_downloaded_bytes_str",
            "_elapsed_str",
        ]
        p = {k: progress[k] for k in fields if k in progress}

        client.set(f"yt-dlp:progress:by-id:{id}", json.dumps(p))
        client.set(f"yt-dlp:progress:by-url-sha256:{url_hash}", json.dumps(p))

        client.set(f"yt-dlp:info:by-id:{id}", json.dumps(progress))
        client.set(f"yt-dlp:info:by-url-sha256:{url_hash}", json.dumps(progress))

    progress_hook = valkey_progress_hook

executor = Executor(
    persister,
    defaults=cast(
        "_Params",
        settings.yt_dlp_defaults | {"logger": Logger(structlog.get_logger("yt-dlp"))},
    ),
    progress_hook=progress_hook,
    logger=structlog.get_logger("executor"),
)

service = create_service(executor, settings.restate_service)

app = restate.app(services=[service], identity_keys=settings.identity_keys)
