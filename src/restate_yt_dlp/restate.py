from typing import Sequence

import restate
from pydantic import BaseModel

from restate_yt_dlp.options import DownloadOptions

from .downloader import Downloader, StateOptions


def create_service(
    downloader: Downloader,
    service_name: str = "yt-dlp",
) -> restate.Service:
    service = restate.Service(service_name)

    register_service(downloader, service)

    return service


class DownloadRequest(BaseModel):
    """Request for downloading a video using yt-dlp."""

    url: str | Sequence[str]
    options: DownloadOptions | None = None
    state: StateOptions | None = None


def register_service(
    downloader: Downloader,
    service: restate.Service | None = None,
):
    service = service or restate.Service("yt-dlp")

    @service.handler()
    async def download(ctx: restate.Context, request: DownloadRequest):
        await ctx.run_typed(
            "download",
            downloader.download,
            url=request.url,
            options=request.options,
            state=request.state,
        )
