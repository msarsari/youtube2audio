"""Shared yt-dlp helpers for querying and downloading YouTube content."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import imageio_ffmpeg
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


YOUTUBE_WATCH_URL = "https://www.youtube.com/watch?v={video_id}"


def get_ffmpeg_location() -> Optional[str]:
    """Return a usable FFmpeg executable path.

    Priority:
    1. YOUTUBE2AUDIO_FFMPEG environment variable
    2. ffmpeg available on PATH
    3. the binary bundled by imageio-ffmpeg
    """
    configured = os.environ.get("YOUTUBE2AUDIO_FFMPEG")
    if configured:
        return configured

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _base_options(ignore_errors: bool = False) -> Dict[str, Any]:
    options: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": ignore_errors,
        "windowsfilenames": True,
    }
    ffmpeg_location = get_ffmpeg_location()
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location
    return options


def extract_info(
    url: str,
    *,
    ignore_errors: bool = False,
    extract_flat: bool = False,
    noplaylist: bool = False,
) -> Dict[str, Any]:
    """Extract metadata without downloading media."""
    options = _base_options(ignore_errors=ignore_errors)
    options.update(
        {
            "skip_download": True,
            "extract_flat": extract_flat,
            "noplaylist": noplaylist,
        }
    )

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as error:
        raise RuntimeError(str(error)) from error

    if not info:
        raise RuntimeError("Could not retrieve YouTube information.")

    return info


def iter_video_entries(info: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Yield video entries from either a video result or playlist result."""
    entries = info.get("entries")
    if entries is None:
        yield info
        return

    for entry in entries:
        if entry:
            yield entry


def video_url_from_info(info: Dict[str, Any]) -> Optional[str]:
    """Return a canonical URL for a yt-dlp video info dictionary."""
    webpage_url = info.get("webpage_url")
    if webpage_url:
        return webpage_url

    url = info.get("url")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return url

    video_id = info.get("id")
    if video_id:
        return YOUTUBE_WATCH_URL.format(video_id=video_id)

    return None


def sanitize_filename(name: str) -> str:
    """Create a Windows-safe filename while keeping Unicode titles."""
    value = (name or "download").strip()
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or "download"


def download_media(
    url: str,
    output_dir: str,
    filename_stem: str,
    *,
    save_as_mp4: bool,
    mp3_quality: str = "320",
) -> str:
    """Download one YouTube item and return the final output path."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    safe_stem = sanitize_filename(filename_stem)
    options = _base_options(ignore_errors=False)
    options.update(
        {
            "noplaylist": True,
            "outtmpl": str(output_path / f"{safe_stem}.%(ext)s"),
            "overwrites": True,
        }
    )

    if save_as_mp4:
        options.update(
            {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    }
                ],
            }
        )
        expected = output_path / f"{safe_stem}.mp4"
    else:
        options.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": mp3_quality,
                    }
                ],
            }
        )
        expected = output_path / f"{safe_stem}.mp3"

    try:
        with YoutubeDL(options) as ydl:
            ydl.extract_info(url, download=True)
    except DownloadError as error:
        raise RuntimeError(str(error)) from error

    if expected.exists():
        return str(expected)

    # Defensive fallback for extractor/container changes.
    candidates = sorted(
        output_path.glob(f"{safe_stem}.*"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        if candidate.suffix.lower() not in {".part", ".ytdl"}:
            return str(candidate)

    raise RuntimeError(f"Download completed but output file was not found for: {filename_stem}")
