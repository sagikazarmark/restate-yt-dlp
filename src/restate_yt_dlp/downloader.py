from __future__ import annotations

import logging
import pathlib
from typing import TYPE_CHECKING, final

import workstate
import workstate.obstore
import yt_dlp
from pydantic import BaseModel

if TYPE_CHECKING:
    from yt_dlp import _Params  # pyright: ignore[reportPrivateUsage]

_logger = logging.getLogger(__name__)


class DownloaderOptions(BaseModel):
    """Options for the downloader."""

    # filter: Filter = Field(default=Filter(), description="File filter options")


class DownloadRequest(BaseModel):
    """Request for downloading a video using yt-dlp."""

    url: str
    prefix: workstate.obstore.Prefix = pathlib.PurePosixPath("")


@final
class Downloader:
    """
    Downloader for videos using yt-dlp and save them to object storage.
    """

    def __init__(
        self,
        state: workstate.StateManager[DownloadRequest],
        base_params: _Params | None = None,  # TODO: expose a custom param object
        options: DownloaderOptions | None = None,
        logger: logging.Logger = _logger,
    ):
        self.state = state
        self.base_params: _Params = base_params.copy() if base_params else {}
        self.options = options or DownloaderOptions()
        self.logger = logger

    @final
    def download(self, request: DownloadRequest):
        logger = logging.LoggerAdapter(self.logger, {"url": request.url})

        logger.info("Downloading video")

        params = self.base_params.copy()

        with self.state.save(request) as output:
            params["paths"] = {"home": output}  # pyright: ignore[reportGeneralTypeIssues]

            with yt_dlp.YoutubeDL(params) as ydl:
                ydl.download([request.url])
