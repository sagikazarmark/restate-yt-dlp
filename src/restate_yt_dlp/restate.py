import restate
from pydantic import BaseModel, Field
from pydantic_restate import ServiceHandlerOptions
from pydantic_restate import ServiceOptions as BaseServiceOptions

from .executor import DownloadRequest, Executor, ExtractInfoRequest, ExtractInfoResponse


class ServiceOptions(BaseServiceOptions):
    name: str = Field(default="yt-dlp")


class HandlerOptions(BaseModel):
    download: ServiceHandlerOptions = Field(
        default_factory=ServiceHandlerOptions,
        description="Options for the download handler",
    )
    extract_info: ServiceHandlerOptions = Field(
        default_factory=lambda: ServiceHandlerOptions(name="extractInfo"),
        description="Options for the extract_info handler",
    )


class Options(BaseModel):
    service: ServiceOptions = Field(default_factory=ServiceOptions)
    handlers: HandlerOptions = Field(default_factory=HandlerOptions)


def create_service(
    downloader: Executor,
    options: Options,
) -> restate.Service:
    service = options.service.new_service()

    register_service(downloader, service, options.handlers)

    return service


def register_service(
    executor: Executor,
    service: restate.Service,
    options: HandlerOptions,
):
    @options.download.handler(service)
    async def download(ctx: restate.Context, request: DownloadRequest):
        await ctx.run_typed(
            "download",
            executor.download,
            id=ctx.request().id,
            request=request,
        )

    @options.extract_info.handler(service)
    async def extract_info(
        ctx: restate.Context,
        request: ExtractInfoRequest,
    ) -> ExtractInfoResponse:
        return await ctx.run_typed(
            "extract_info",
            executor.extract_info,
            id=ctx.request().id,
            request=request,
        )
