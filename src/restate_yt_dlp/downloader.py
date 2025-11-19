from __future__ import annotations

import logging
import pathlib
from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

import workstate
import yt_dlp
from pydantic import BaseModel
from workstate.obstore import IncludeExcludeFilter, Prefix

from .options2 import DownloadOptions

if TYPE_CHECKING:
    from yt_dlp import _Params

_logger = logging.getLogger(__name__)


class StateOptions(BaseModel):
    prefix: Prefix = pathlib.PurePosixPath("")
    filter: IncludeExcludeFilter | None = None


class Downloader:
    """
    Downloader for videos using yt-dlp and save them to object storage.
    """

    def __init__(
        self,
        state: workstate.StateManager[StateOptions | None],
        defaults: _Params | None = None,
        logger: logging.Logger = _logger,
    ):
        self.state = state
        self.defaults: _Params = defaults.copy() if defaults else {}
        self.logger = logger

    def download(
        self,
        url: str | Sequence[str],
        options: DownloadOptions | None = None,
        state: StateOptions | None = None,
    ):
        logger = logging.LoggerAdapter(
            self.logger,
            {"url": url},
            merge_extra=True,
        )

        logger.info("Downloading video")

        with self.state.save(state) as output:
            params = cast(
                "_Params",
                {**self.defaults.copy(), **(options or {}), "paths": {"home": output}},
            )

            yt_dlp.YoutubeDL(params).download(url)

            logger.info("Downloading video completed")
