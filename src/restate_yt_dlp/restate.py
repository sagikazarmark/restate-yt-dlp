from __future__ import annotations

import restate

from .downloader import Downloader, DownloadRequest


def create_service(
    downloader: Downloader,
    service_name: str = "yt-dlp",
) -> restate.Service:
    service = restate.Service(service_name)

    register_service(downloader, service)

    return service


def register_service(
    downloader: Downloader,
    service: restate.Service | None = None,
):
    service = service or restate.Service("yt-dlp")

    @service.handler()
    async def download(ctx: restate.Context, request: DownloadRequest):
        await ctx.run_typed("download", downloader.download, request=request)
