import restate

from .executor import DownloadRequest, Executor


def create_service(
    downloader: Executor,
    service_name: str = "yt-dlp",
) -> restate.Service:
    service = restate.Service(service_name)

    register_service(downloader, service)

    return service


def register_service(
    executor: Executor,
    service: restate.Service,
):
    @service.handler()
    async def download(ctx: restate.Context, request: DownloadRequest):
        await ctx.run_typed("download", executor.download, request=request)
