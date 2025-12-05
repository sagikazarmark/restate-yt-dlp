from datetime import timedelta
from typing import Dict

import restate
from pydantic import BaseModel, Field

from .executor import DownloadRequest, Executor


class ServiceOptions(BaseModel):
    name: str = Field(default="yt-dlp", description="Name of the service")
    description: str | None = Field(
        default=None,
        description="Documentation as shown in the UI, Admin REST API, and the generated OpenAPI documentation of this service.",
    )
    metadata: Dict[str, str] | None = Field(
        default=None,
        description="Service metadata, as propagated in the Admin REST API.",
    )
    inactivity_timeout: timedelta | None = Field(
        default=None,
        description=(
            "This timer guards against stalled invocations. Once it expires, Restate triggers a graceful"
            "termination by asking the invocation to suspend (which preserves intermediate progress)."
            "The abortTimeout is used to abort the invocation, in case it doesn't react to the request to suspend."
            "This overrides the default inactivity timeout configured in the restate-server for all invocations to this service."
        ),
    )
    abort_timeout: timedelta | None = Field(
        default=None,
        description=(
            "This timer guards against stalled service/handler invocations that are supposed to terminate. The"
            "abort timeout is started after the inactivityTimeout has expired and the service/handler invocation has been asked to gracefully terminate."
            "Once the timer expires, it will abort the service/handler invocation."
            "This timer potentially *interrupts* user code. If the user code needs longer to gracefully terminate, then this value needs to be set accordingly."
            "This overrides the default abort timeout configured in the restate-server for all invocations to this service."
        ),
    )
    journal_retention: timedelta | None = Field(
        default=None,
        description=(
            "The journal retention. When set, this applies to all requests to all handlers of this service."
            "In case the request has an idempotency key, the idempotencyRetention caps the journal retention time."
        ),
    )
    idempotency_retention: timedelta | None = Field(
        default=None,
        description="The retention duration of idempotent requests to this service.",
    )
    ingress_private: bool | None = Field(
        default=None,
        description=(
            "When set to True this service, with all its handlers, cannot be invoked from the restate-server"
            "HTTP and Kafka ingress, but only from other services."
        ),
    )
    invocation_retry_policy: restate.InvocationRetryPolicy | None = Field(
        default=None,
        description="The retry policy for failed invocations of this service.",
    )

    def new_service(self) -> restate.Service:
        return restate.Service(
            self.name,
            description=self.description,
            metadata=self.metadata,
            inactivity_timeout=self.inactivity_timeout,
            abort_timeout=self.abort_timeout,
            journal_retention=self.journal_retention,
            idempotency_retention=self.idempotency_retention,
            ingress_private=self.ingress_private,
            invocation_retry_policy=self.invocation_retry_policy,
        )


def create_service(downloader: Executor, options: ServiceOptions) -> restate.Service:
    service = options.new_service()

    register_service(downloader, service)

    return service


def register_service(executor: Executor, service: restate.Service):
    @service.handler()
    async def download(ctx: restate.Context, request: DownloadRequest):
        await ctx.run_typed(
            "download",
            executor.download,
            id=ctx.request().id,
            request=request,
        )
