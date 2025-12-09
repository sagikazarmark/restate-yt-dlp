import json
from pathlib import Path

from glide_sync import GlideClient

from .restate_yt_dlp import Progress


class ValkeyProgressHook:
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

        if id:
            self.client.set(f"yt-dlp:download:info:by-id:{id}", info_json)
            self.client.set(f"yt-dlp:download:progress:by-id:{id}", progress_json)

            if filename:
                self.client.hset(
                    f"yt-dlp:download:downloaded-bytes:by-id:{id}",
                    {filename: downloaded_bytes},
                )

        self.client.set(f"yt-dlp:download:info:by-url:{url}", info_json)
        self.client.set(f"yt-dlp:download:progress:by-url:{url}", progress_json)

        if filename:
            self.client.hset(
                f"yt-dlp:download:downloaded-bytes:by-url:{url}",
                {filename: downloaded_bytes},
            )

        self.client.set(
            f"yt-dlp:download:info:by-invocation-id:{invocation_id}", info_json
        )
        self.client.set(
            f"yt-dlp:download:progress:by-invocation-id:{invocation_id}",
            progress_json,
        )

        if filename:
            self.client.hset(
                f"yt-dlp:download:downloaded-bytes:by-invocation-id:{invocation_id}",
                {filename: downloaded_bytes},
            )
