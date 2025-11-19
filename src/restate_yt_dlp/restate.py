from typing import Sequence, cast

import restate
from pydantic import BaseModel

from restate_yt_dlp.options import DownloadOptions
from restate_yt_dlp.options2 import DownloadOptions as DownloadOptions2

from .downloader import Downloader, StateOptions


def create_service(
    downloader: Downloader,
    service_name: str = "yt-dlp",
) -> restate.Service:
    service = restate.Service(service_name)

    register_service(downloader, service)

    return service


def register_service(
    downloader: Downloader,
    service: restate.Service,
):
    class DownloadRequest(BaseModel):
        """Request for downloading a video using yt-dlp."""

        url: str | Sequence[str]
        options: DownloadOptions | None = None
        state: StateOptions | None = None

    @service.handler()
    async def download(ctx: restate.Context, request: DownloadRequest):
        await ctx.run_typed(
            "download",
            downloader.download,
            url=request.url,
            options=cast(
                DownloadOptions2,
                request.options and request.options.model_dump(exclude_none=True),
            ),
            state=request.state,
        )
