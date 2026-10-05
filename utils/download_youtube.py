"""Download and tag YouTube media."""

from __future__ import annotations

import os

import requests
from mutagen.id3 import APIC, ID3, TALB, TCON, TIT2, TPE1
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover

from utils.ytdlp_service import YOUTUBE_WATCH_URL, download_media


def thread_query_youtube(args):
    """Download a YouTube item and apply metadata.

    The argument structure is kept compatible with the existing threaded UI:
    ((title, video_dict), (download_path, legacy_temp_path), song_properties, save_as_mp4)
    """
    _, videos_dict = args[0]
    download_path, _legacy_temp_path = args[1]
    song_properties = args[2]
    save_as_mp4 = args[3]

    full_link = videos_dict.get("webpage_url") or YOUTUBE_WATCH_URL.format(video_id=videos_dict["id"])
    output_file = download_media(
        full_link,
        download_path,
        song_properties.get("song") or videos_dict.get("id") or "download",
        save_as_mp4=save_as_mp4,
    )

    set_song_metadata(
        os.path.dirname(output_file),
        song_properties,
        os.path.basename(output_file),
        save_as_mp4,
    )
    return output_file


def set_song_metadata(directory, song_properties, song_filename, save_as_mp4):
    """Set song metadata and optional cover artwork."""

    response = _get_artwork(song_properties.get("artwork"))

    if save_as_mp4:
        _write_mp4_metadata(directory, song_properties, song_filename, response)
    else:
        _write_mp3_metadata(directory, song_properties, song_filename, response)


def _get_artwork(artwork_url):
    if not artwork_url or artwork_url == "Unknown":
        return None

    try:
        response = requests.get(artwork_url, timeout=(2, 8))
        response.raise_for_status()
        return response
    except requests.RequestException:
        return None


def _is_jpeg(response):
    return response is not None and response.content[:3] == b"\xff\xd8\xff"


def _is_png(response):
    return response is not None and response.content[:8] == b"\x89PNG\r\n\x1a\n"


def _write_mp4_metadata(directory, song_properties, song_filename, response):
    """Add metadata to an MP4/M4A container."""
    audio = MP4(os.path.join(directory, song_filename))
    if audio.tags is None:
        audio.add_tags()

    audio.tags["\xa9alb"] = [song_properties.get("album") or "Unknown"]
    audio.tags["\xa9ART"] = [song_properties.get("artist") or "Unknown"]
    audio.tags["\xa9nam"] = [song_properties.get("song") or "Unknown"]
    audio.tags["\xa9gen"] = [song_properties.get("genre") or "Unknown"]

    if _is_jpeg(response):
        audio.tags["covr"] = [MP4Cover(response.content, imageformat=MP4Cover.FORMAT_JPEG)]
    elif _is_png(response):
        audio.tags["covr"] = [MP4Cover(response.content, imageformat=MP4Cover.FORMAT_PNG)]

    audio.save()


def _write_mp3_metadata(directory, song_properties, song_filename, response):
    """Add ID3 metadata to an MP3 file."""
    filepath = os.path.join(directory, song_filename)
    audio = MP3(filepath, ID3=ID3)

    if audio.tags is None:
        audio.add_tags()

    audio.tags.setall("TALB", [TALB(encoding=3, text=song_properties.get("album") or "Unknown")])
    audio.tags.setall("TPE1", [TPE1(encoding=3, text=song_properties.get("artist") or "Unknown")])
    audio.tags.setall("TIT2", [TIT2(encoding=3, text=song_properties.get("song") or "Unknown")])
    audio.tags.setall("TCON", [TCON(encoding=3, text=song_properties.get("genre") or "Unknown")])

    if _is_jpeg(response):
        audio.tags.setall(
            "APIC",
            [
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=response.content,
                )
            ],
        )
    elif _is_png(response):
        audio.tags.setall(
            "APIC",
            [
                APIC(
                    encoding=3,
                    mime="image/png",
                    type=3,
                    desc="Cover",
                    data=response.content,
                )
            ],
        )

    audio.save()
