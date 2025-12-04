from urllib.parse import parse_qs, urlparse


def get_youtube_video_id(url: str) -> str | None:
    # Handle youtu.be short links
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]

    # Handle standard youtube.com links
    parsed = urlparse(url)
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]

    return None
