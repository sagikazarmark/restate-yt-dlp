import json
from pathlib import Path

from glide_sync import Batch, GlideClient

from .restate_yt_dlp import Progress


class ValkeyProgressHook:
    # Key patterns
    KEY_PREFIX = "yt-dlp:download"
    INFO_KEY = "info"
    PROGRESS_KEY = "progress"
    DOWNLOADED_BYTES_KEY = "downloaded-bytes"

    # Fields to extract for progress updates
    PROGRESS_FIELDS = frozenset(
        [
            "status",
            "downloaded_bytes",
            "total_bytes",
            "total_bytes_estimate",
            "elapsed",
            "eta",
            "speed",
            "_percent_str",
            "_speed_str",
            "_eta_str",
            "_total_bytes_str",
            "_total_bytes_estimate_str",
            "_downloaded_bytes_str",
            "_elapsed_str",
        ]
    )

    def __init__(self, client: GlideClient):
        self.client = client

    def _make_key(self, key_type: str, identifier_type: str, identifier: str) -> str:
        """Generate a Redis key with consistent pattern."""
        return f"{self.KEY_PREFIX}:{key_type}:{identifier_type}:{identifier}"

    def __call__(self, invocation_id: str, url: str, progress: Progress):
        id = progress.get("info_dict", {}).get("id", None)

        partial_progress = {
            k: progress[k] for k in self.PROGRESS_FIELDS if k in progress
        }

        info_json = json.dumps(progress)
        progress_json = json.dumps(partial_progress)

        filename = progress.get("filename", None)
        if filename:
            filename = Path(filename).name

        downloaded_bytes = str(progress.get("downloaded_bytes", 0))

        pipeline = Batch(is_atomic=False)

        # Store data by different identifiers
        identifiers = [
            ("by-url", url),
            ("by-invocation-id", invocation_id),
        ]

        if id:
            identifiers.append(("by-id", id))

        for identifier_type, identifier in identifiers:
            pipeline.set(
                self._make_key(self.INFO_KEY, identifier_type, identifier), info_json
            )
            pipeline.set(
                self._make_key(self.PROGRESS_KEY, identifier_type, identifier),
                progress_json,
            )

            if filename:
                pipeline.hset(
                    self._make_key(
                        self.DOWNLOADED_BYTES_KEY, identifier_type, identifier
                    ),
                    {filename: downloaded_bytes},
                )

        self.client.exec(pipeline, False)
