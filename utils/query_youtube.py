"""YouTube metadata queries powered by yt-dlp."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

from utils.ytdlp_service import extract_info, iter_video_entries, video_url_from_info


def get_youtube_content(youtube_url, override_error):
    """Parse a YouTube video/playlist URL and return UI-compatible metadata."""
    try:
        info = extract_info(
            youtube_url,
            ignore_errors=override_error,
            extract_flat=False,
            noplaylist=False,
        )
    except RuntimeError:
        if override_error:
            return {}
        raise

    return video_content_to_dict(iter_video_entries(info))


def get_playlist_video_info(playlist_url):
    """Return canonical URLs for videos found in a playlist."""
    info = extract_info(
        playlist_url,
        ignore_errors=True,
        extract_flat=True,
        noplaylist=False,
    )

    urls = []
    for entry in iter_video_entries(info):
        url = video_url_from_info(entry)
        if url:
            urls.append(url)

    return tuple(urls)


def get_video_info(args):
    """Get metadata for a single YouTube video.

    The tuple signature is preserved for compatibility with the existing UI/tests.
    """
    video_url, override_error = args

    try:
        return extract_info(
            video_url,
            ignore_errors=override_error,
            extract_flat=False,
            noplaylist=True,
        )
    except RuntimeError:
        if override_error:
            return {}
        raise


def video_content_to_dict(vid_info_list):
    """Convert yt-dlp video info dictionaries to the structure expected by the UI.

    Duplicate titles are disambiguated so playlist entries are never overwritten.
    """
    result: Dict[str, Dict[str, object]] = {}

    for video in vid_info_list:
        if not video:
            continue

        video_id = video.get("id")
        if not video_id:
            continue

        title = str(video.get("title") or video_id)
        display_title = title
        suffix = 2
        while display_title in result:
            display_title = f"{title} ({suffix})"
            suffix += 1

        result[display_title] = {
            "id": str(video_id),
            "duration": video.get("duration") or 0,
            "webpage_url": video_url_from_info(video),
            "thumbnail": video.get("thumbnail"),
            "channel": video.get("channel") or video.get("uploader"),
        }

    return result
