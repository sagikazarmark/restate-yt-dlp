from typing import Any, TypedDict


class Progress(TypedDict, total=False):
    """Type definition for yt-dlp progress hook dictionary."""

    status: str  # Required: 'downloading', 'finished', 'error'

    # Download progress fields
    downloaded_bytes: int
    total_bytes: int
    total_bytes_estimate: int
    elapsed: float
    eta: float
    speed: float

    # Formatted strings
    _percent_str: str
    _speed_str: str
    _eta_str: str
    _total_bytes_str: str
    _total_bytes_estimate_str: str
    _downloaded_bytes_str: str
    _elapsed_str: str

    # File information
    filename: str
    tmpfilename: str

    # Video information
    info_dict: dict[str, Any]

    # Additional fields
    fragment_index: int
    fragment_count: int
