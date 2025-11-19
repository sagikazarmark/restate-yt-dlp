from pathlib import PurePosixPath
from typing import Annotated, Mapping, TypedDict

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field


def validate_path_string(value) -> str:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("Path cannot be empty")
    return value


def validate_no_parent_refs(path: PurePosixPath) -> PurePosixPath:
    if path.is_absolute():
        raise ValueError("Path must be relative")
    if ".." in path.parts:
        raise ValueError('Path cannot contain ".." components')
    return path


SafeRelativePath = Annotated[
    PurePosixPath,
    BeforeValidator(validate_path_string),
    AfterValidator(validate_no_parent_refs),
]


class DownloadOptions(BaseModel):
    # Format selection
    format: str | None = Field(
        default=None,
        description="Video format code or function for format selection",
    )
    allow_unplayable_formats: bool | None = Field(
        default=None,
        description="Allow unplayable formats to be extracted and downloaded",
    )
    format_sort: list[str] | None = Field(
        default=None,
        description="A list of fields by which to sort the video formats",
    )
    format_sort_force: bool | None = Field(
        default=None,
        description="Force the given format_sort",
    )

    # Output templates and paths
    outtmpl: SafeRelativePath | Mapping[str, SafeRelativePath] | None = Field(
        default=None,
        description="Dictionary of templates for output names or single string for compatibility",
    )
    outtmpl_na_placeholder: str | None = Field(
        default=None,
        description="Placeholder for unavailable meta fields",
    )
    restrictfilenames: bool | None = Field(
        default=None,
        description="Do not allow '&' and spaces in file names",
    )
    windowsfilenames: bool | None = Field(
        default=None,
        description="Force filenames to be Windows compatible (True) or sanitize minimally (False)",
    )
    trim_file_name: int | None = Field(
        default=None,
        description="Limit length of filename (extension excluded)",
    )

    updatetime: bool | None = Field(
        default=None,
        description="Use the Last-modified header to set the file modification time",
    )
    writedescription: bool | None = Field(
        default=None,
        description="Write the video description to a .description file",
    )
    writeinfojson: bool | None = Field(
        default=None,
        description="Write the video description to a .info.json file",
    )
    allow_playlist_files: bool | None = Field(
        default=None,
        description="Whether to write playlists' description, infojson etc also to disk when using the 'write*' options",
    )
    clean_infojson: bool | None = Field(
        default=None,
        description="Remove internal metadata from the infojson",
    )
    getcomments: bool | None = Field(
        default=None,
        description="Extract video comments. This will not be written to disk unless writeinfojson is also given",
    )
    writethumbnail: bool | None = Field(
        default=None,
        description="Write the thumbnail image to a file",
    )
    write_all_thumbnails: bool | None = Field(
        default=None,
        description="Write all thumbnail formats to files",
    )
    writelink: bool | None = Field(
        default=None,
        description="Write an internet shortcut file, depending on the current platform (.url/.webloc/.desktop)",
    )
    writeurllink: bool | None = Field(
        default=None,
        description="Write a Windows internet shortcut file (.url)",
    )
    writewebloclink: bool | None = Field(
        default=None,
        description="Write a macOS internet shortcut file (.webloc)",
    )
    writedesktoplink: bool | None = Field(
        default=None,
        description="Write a Linux internet shortcut file (.desktop)",
    )

    # Subtitle options
    writesubtitles: bool | None = Field(
        default=None,
        description="Write the video subtitles to a file",
    )
    writeautomaticsub: bool | None = Field(
        default=None,
        description="Write the automatically generated subtitles to a file",
    )
    subtitlesformat: str | None = Field(
        default=None,
        description="The format code for subtitles",
    )
    subtitleslangs: list[str] | None = Field(
        default=None,
        description="List of languages of the subtitles to download (can be regex). The list may contain 'all'",
    )

    # Filtering
    matchtitle: bool | None = Field(
        default=None,
        description="Download only matching titles",
    )
    rejecttitle: bool | None = Field(
        default=None,
        description="Reject downloads for matching titles",
    )
    prefer_free_formats: bool | None = Field(
        default=None,
        description="Whether to prefer video formats with free containers over non-free ones of the same quality",
    )
    keepvideo: str | None = Field(
        default=None,
        description="Keep the video file after post-processing",
    )

    ## File size limits
    min_filesize: int | None = Field(
        default=None,
        description="Abort download if filesize is smaller than SIZE",
    )
    max_filesize: int | None = Field(
        default=None,
        description="Abort download if filesize is larger than SIZE",
    )

    ## View count filtering
    min_views: str | None = Field(
        default=None,
        description="An integer representing the minimum view count the video must have",
    )
    max_views: str | None = Field(
        default=None,
        description="An integer representing the maximum view count",
    )

    # Miscellaneous
    useid: bool | None = Field(
        default=None,
        description="Use the video ID in the file name",
    )


class DownloadOptionsDict(TypedDict, total=False):
    """TypedDict version of DownloadOptions for use without Pydantic validation."""

    # Format selection
    format: str | None
    allow_unplayable_formats: bool | None
    format_sort: list[str] | None
    format_sort_force: bool | None

    # Output templates and paths
    outtmpl: SafeRelativePath | Mapping[str, SafeRelativePath] | None
    outtmpl_na_placeholder: str | None
    restrictfilenames: bool | None
    windowsfilenames: bool | None
    trim_file_name: int | None

    updatetime: bool | None
    writedescription: bool | None
    writeinfojson: bool | None
    allow_playlist_files: bool | None
    clean_infojson: bool | None
    getcomments: bool | None
    writethumbnail: bool | None
    write_all_thumbnails: bool | None
    writelink: bool | None
    writeurllink: bool | None
    writewebloclink: bool | None
    writedesktoplink: bool | None

    # Subtitle options
    writesubtitles: bool | None
    writeautomaticsub: bool | None
    subtitlesformat: str | None
    subtitleslangs: list[str] | None

    # Filtering
    matchtitle: bool | None
    rejecttitle: bool | None
    prefer_free_formats: bool | None
    keepvideo: str | None

    # File size limits
    min_filesize: int | None
    max_filesize: int | None

    # View count filtering
    min_views: str | None
    max_views: str | None

    # Miscellaneous
    useid: bool | None
