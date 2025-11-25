from __future__ import annotations

import logging
import tempfile
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path, PurePath, PurePosixPath
from typing import TYPE_CHECKING, Protocol, cast

import pathspec
import yt_dlp
from pydantic import AnyUrl, BaseModel, ConfigDict, DirectoryPath, Field

from .options import DownloadOptions

if TYPE_CHECKING:
    from yt_dlp import _Params

_logger = logging.getLogger(__name__)


class DownloadRequest(BaseModel):
    """Request for downloading one or more videos using yt-dlp."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://www.youtube.com/watch?v=_fjbR0qKT8w",
                    "output": {
                        "ref": "s3://bucket/videoid/",
                    },
                    "options": {},
                },
            ]
        }
    )

    url: str | Sequence[str] = Field(description="URL(s) to download")
    output: DownloadRequestOutput
    options: DownloadOptions | None = Field(
        default=None, description="Download options"
    )


class DownloadRequestOutput(BaseModel):
    ref: AnyUrl | PurePosixPath = Field(
        description="Output reference for downloaded content",
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


class Executor:
    def __init__(
        self,
        persister: DirectoryPersister,
        defaults: _Params | None = None,
        logger: logging.Logger = _logger,
    ):
        self.persister = persister
        self.defaults: _Params = defaults.copy() if defaults else {}
        self.logger = logger

    def download(
        self,
        request: DownloadRequest,
    ):
        logger = logging.LoggerAdapter(
            self.logger,
            {"url": request.url},
            merge_extra=True,
        )

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
                },
            )

            yt_dlp.YoutubeDL(params).download(request.url)

            logger.info("Downloading video completed")

            self.persister.persist(
                request.output.ref,
                Path(tmpdir),
                request.output.filter,
            )
