from datetime import timedelta

import restate

from .executor import DownloadRequest, Executor


def create_service(
    downloader: Executor,
    service_name: str = "yt-dlp",
    inactivity_timeout: timedelta | None = None,
    abort_timeout: timedelta | None = None,
) -> restate.Service:
    service = restate.Service(
        service_name,
        inactivity_timeout=inactivity_timeout,
        abort_timeout=abort_timeout,
    )

    register_service(downloader, service)

    return service


def register_service(
    executor: Executor,
    service: restate.Service,
):
    @service.handler()
    async def download(ctx: restate.Context, request: DownloadRequest):
        await ctx.run_typed("download", executor.download, request=request)
