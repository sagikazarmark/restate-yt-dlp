from __future__ import annotations

import logging
import pathlib
from typing import TYPE_CHECKING, Any, cast, final

import workstate
import workstate.obstore
import yt_dlp
from pydantic import BaseModel

if TYPE_CHECKING:
    from yt_dlp import _Params

_logger = logging.getLogger(__name__)


class DownloadRequest(BaseModel):
    """Request for downloading a video using yt-dlp."""

    url: str
    params: dict[str, Any] | None = None
    state: StateOptions | None = None


class StateOptions(BaseModel):
    prefix: workstate.obstore.Prefix = pathlib.PurePosixPath("")
    filter: workstate.obstore.IncludeExcludeFilter | None = None


@final
class Downloader:
    """
    Downloader for videos using yt-dlp and save them to object storage.
    """

    def __init__(
        self,
        state: workstate.StateManager[StateOptions | None],
        default_params: _Params | None = None,
        override_params: _Params | None = None,
        logger: logging.Logger = _logger,
    ):
        self.state = state
        self.default_params: _Params = default_params.copy() if default_params else {}
        self.override_params: _Params = (
            override_params.copy() if override_params else {}
        )
        self.logger = logger

    @final
    def download(self, request: DownloadRequest):
        logger = logging.LoggerAdapter(
            self.logger,
            {"url": request.url},
            merge_extra=True,
        )

        logger.info("Downloading video")

        params = cast(
            "_Params",
            self.default_params.copy()
            | (request.params or {})
            | self.override_params.copy(),
        )

        with self.state.save(request.state) as output:
            params["paths"] = {"home": output}  # pyright: ignore[reportGeneralTypeIssues]

            with yt_dlp.YoutubeDL(params) as ydl:
                ydl.download([request.url])
