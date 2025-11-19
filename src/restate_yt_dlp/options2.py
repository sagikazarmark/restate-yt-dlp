from typing import Mapping, TypedDict

from .options import SafeRelativePath


class DownloadOptions(TypedDict, total=False):
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
