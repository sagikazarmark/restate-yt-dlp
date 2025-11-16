from __future__ import annotations

from datetime import timedelta

import restate

from .downloader import Downloader, DownloadRequest


def create_service(
    downloader: Downloader,
    service_name: str = "YoutubeDownloader",
) -> restate.Service:
    service = restate.Service(service_name)

    register_service(downloader, service)

    return service


def register_service(
    downloader: Downloader,
    service: restate.Service | None = None,
):
    service = service or restate.Service("YoutubeDownloader")

    @service.handler(  # pyright: ignore [reportUnknownMemberType, reportUntypedFunctionDecorator]
        # TODO: make this configurable?
        inactivity_timeout=timedelta(minutes=30),
        abort_timeout=timedelta(minutes=30),
    )
    async def download(  # pyright: ignore [reportUnusedFunction]
        ctx: restate.Context,
        request: DownloadRequest,
    ):
        _ = await ctx.run_typed("download", downloader.download, request=request)
