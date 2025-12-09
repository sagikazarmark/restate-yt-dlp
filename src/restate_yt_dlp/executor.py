from __future__ import annotations

import logging
import tempfile
from functools import cached_property
from pathlib import Path, PurePath, PurePosixPath
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    Protocol,
    Required,
    TypedDict,
    cast,
)

import pathspec
import yt_dlp
from pydantic import AnyUrl, BaseModel, ConfigDict, DirectoryPath, Field
from restate.exceptions import TerminalError
from yt_dlp.networking.exceptions import HTTPError, TransportError
from yt_dlp.utils import (
    DownloadError,
    ExtractorError,
    UnavailableVideoError,
    UnsupportedError,
)

from .options import RequestOptions
from .progress import Progress

if TYPE_CHECKING:
    from yt_dlp import _Params

_logger = logging.getLogger(__name__)


class DownloadRequest(BaseModel):
    """Request for downloading a videos using yt-dlp."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://www.youtube.com/watch?v=_fjbR0qKT8w",
                    "output": {
                        "destination": "s3://bucket/videoid/",
                    },
                    "options": {},
                },
            ]
        }
    )

    url: str = Field(description="URL to download")
    output: DownloadRequestOutput
    options: RequestOptions | None = Field(default=None, description="Download options")


class ExtractInfoRequest(BaseModel):
    """Request for extracting information using yt-dlp."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://www.youtube.com/watch?v=_fjbR0qKT8w",
                    "options": {},
                },
            ]
        }
    )

    url: str = Field(description="URL to extract information from")
    options: RequestOptions | None = Field(default=None)


class ExtractInfoResponse(TypedDict, total=False):
    age_limit: int
    availability: (
        Literal[
            "private",
            "premium_only",
            "subscriber_only",
            "needs_auth",
            "unlisted",
            "public",
        ]
        | None
    )
    available_at: int
    creator: str | None
    comment_count: int | None
    duration: int | None
    formats: list[dict[str, Any]] | None
    id: Required[str]
    like_count: int | None
    tags: list[str] | None
    thumbnail: str | None
    timestamp: int | float | None
    title: str | None
    uploader: str | None
    url: str | None


class DownloadRequestOutput(BaseModel):
    destination: AnyUrl | PurePosixPath = Field(
        description="Output destination for downloaded content",
        examples=["s3://bucket/videoid/"],
        union_mode="left_to_right",  # This is important to keep best match order (TODO: consider using a custom discriminator)
    )
    filter: IncludeExcludeFilter | None = Field(
        default=None, description="Filter for which files to upload using glob patterns"
    )


class IncludeExcludeFilter(BaseModel):
    """Filter for which files to upload using glob patterns."""

    include: list[str] = Field(
        default=[],
        description="List of glob patterns to include",
        examples=[[], ["*.mp4", "**/*.webm"]],
    )
    exclude: list[str] = Field(
        default=[],
        description="List of glob patterns to exclude",
        examples=[[], ["**/*.pdf"]],
    )

    @cached_property
    def _exclude_spec(self) -> pathspec.PathSpec | None:
        """Cached PathSpec for exclude patterns."""
        if not self.exclude:
            return None
        return pathspec.PathSpec.from_lines("gitwildmatch", self.exclude)

    @cached_property
    def _include_spec(self) -> pathspec.PathSpec | None:
        """Cached PathSpec for include patterns."""
        if not self.include:
            return None
        return pathspec.PathSpec.from_lines("gitwildmatch", self.include)

    def match(self, path: PurePath) -> bool:
        """
        Check if a file should be uploaded based on the filter.

        Args:
            path: The relative path of the file.

        Returns:
            True if the file should be uploaded, False otherwise.
        """

        path_str = path.as_posix()

        # Check exclude patterns first
        if self._exclude_spec and self._exclude_spec.match_file(path_str):
            return False

        # If include patterns exist, path must match at least one
        if self._include_spec and not self._include_spec.match_file(path_str):
            return False

        return True


class PathFilter(Protocol):
    def match(self, path: PurePath) -> bool: ...


class DirectoryPersister(Protocol):
    def persist(
        self,
        ref: AnyUrl | PurePosixPath,
        src: DirectoryPath,
        filter: PathFilter | None = None,
    ): ...


type ProgressHook = Callable[[str, str, Progress], None]


class Executor:
    def __init__(
        self,
        persister: DirectoryPersister,
        defaults: _Params | None = None,
        progress_hook: ProgressHook | None = None,
        logger: logging.Logger = _logger,
    ):
        self.persister = persister
        self.defaults: _Params = defaults.copy() if defaults else {}
        self.progress_hook = progress_hook
        self.logger = logger

    def download(
        self,
        id: str,
        request: DownloadRequest,
    ):
        logger = logging.LoggerAdapter(
            self.logger,
            {"id": id, "url": request.url},
            merge_extra=True,
        )

        def progress_hook(progress: Progress):
            if self.progress_hook:
                self.progress_hook(id, request.url, progress)

        logger.info("Downloading video")

        with tempfile.TemporaryDirectory() as tmpdir:
            params = cast(
                "_Params",
                {
                    **self.defaults.copy(),
                    **(
                        request.options.model_dump(exclude_none=True)
                        if request.options
                        else {}
                    ),
                    "paths": {"home": tmpdir},
                    "progress_hooks": [progress_hook],
                },
            )

            yt_dlp.YoutubeDL(params).download(request.url)

            logger.info("Downloading video completed")

            self.persister.persist(
                request.output.destination,
                Path(tmpdir),
                request.output.filter,
            )

    def extract_info(
        self,
        id: str,
        request: ExtractInfoRequest,
    ) -> ExtractInfoResponse:
        logger = logging.LoggerAdapter(
            self.logger,
            {"id": id, "url": request.url},
            merge_extra=True,
        )

        logger.info("Extracting video info")

        params = cast(
            "_Params",
            {
                **self.defaults.copy(),
                **(
                    request.options.model_dump(exclude_none=True)
                    if request.options
                    else {}
                ),
            },
        )

        try:
            info = yt_dlp.YoutubeDL(params).extract_info(request.url, download=False)
        except (DownloadError, ExtractorError) as err:
            if is_retryable_error(err):
                # Re-raise retryable errors - Restate will retry them
                raise
            else:
                # Wrap non-retryable errors in TerminalError
                # Extract the actual error message
                actual_exception = getattr(err, "exc_info", [None, None])[1]
                error_msg = str(actual_exception) if actual_exception else str(err)

                raise TerminalError(error_msg, status_code=422) from err

        except Exception as err:
            # Catch any other unexpected errors
            # Be conservative - treat unknown errors as non-retryable
            raise TerminalError(
                f"Unexpected error during download: {type(err).__name__}: {err}",
            )

        logger.info("Extracting video info completed")

        return info


def is_retryable_error(err):
    """
    Determine if a yt-dlp error is retryable.

    For DownloadError/ExtractorError, checks the wrapped exception in exc_info[1].
    """
    # Get the actual exception to check
    actual_exception = (
        getattr(err, "exc_info", [None, None])[1] if hasattr(err, "exc_info") else err
    )

    # If no wrapped exception, use the error itself
    if actual_exception is None:
        actual_exception = err

    # Retryable network/transport errors
    if isinstance(actual_exception, (TransportError, UnavailableVideoError)):
        return True

    # HTTPError: 5xx are retryable (except 501), 4xx are not
    if isinstance(actual_exception, HTTPError):
        status = actual_exception.status
        # 503 Service Unavailable, 502 Bad Gateway, 504 Gateway Timeout are retryable
        if status in (502, 503, 504, 429):  # 429 = Too Many Requests
            return True
        # 408 Request Timeout
        if status == 408:
            return True
        # Other 5xx might be retryable (server errors)
        if 500 <= status < 600 and status != 501:  # 501 Not Implemented is permanent
            return True
        # All 4xx are non-retryable (client errors)
        return False

    # All ExtractorError types are non-retryable (parsing/extraction failures)
    if isinstance(actual_exception, (ExtractorError, UnsupportedError)):
        return False

    # Connection/socket errors (these would be wrapped in TransportError, but just in case)
    import socket

    if isinstance(actual_exception, (socket.timeout, socket.error)):
        return True

    # DNS errors
    if isinstance(actual_exception, OSError):
        # Network unreachable, connection refused, etc.
        if actual_exception.errno in (
            101,
            111,
            104,
            113,
        ):  # ENETUNREACH, ECONNREFUSED, ECONNRESET, EHOSTUNREACH
            return True

    # Default: assume non-retryable for safety
    return False
