# youtube2audio

A desktop GUI application for downloading YouTube videos or playlists as tagged MP3 or MP4 files.

## What changed in this fork

The media backend has been modernized around **yt-dlp + FFmpeg**:

- yt-dlp handles video/playlist metadata and downloads.
- FFmpeg handles MP3 extraction and MP4 conversion/merging.
- `imageio-ffmpeg` provides an FFmpeg binary automatically when a system FFmpeg installation is not available.
- Legacy `youtube-dl`, `pytube`, `pytubefix`, and MoviePy download/conversion paths were removed.
- MP4 now produces a real `.mp4` file instead of copying a video stream to a `.m4a` filename.
- Existing iTunes "Ask butler" metadata suggestions and cover embedding are preserved.

## Features

- Load a single YouTube video or a playlist.
- Edit title, album, artist, genre, and artwork before downloading.
- Use "Ask butler" to query iTunes for metadata suggestions.
- Save audio as MP3 (currently 320 kbps).
- Save video as MP4.
- Embed metadata and supported JPEG/PNG artwork.
- Keep the GUI responsive while downloads run in a background Qt thread.

## Requirements

- Python 3.10+
- Windows, Linux, or macOS
- Internet access

FFmpeg is resolved in this order:

1. `YOUTUBE2AUDIO_FFMPEG` environment variable
2. `ffmpeg` available on PATH
3. the binary bundled by `imageio-ffmpeg`

## Run on Windows

```powershell
git clone https://github.com/msarsari/youtube2audio.git
cd youtube2audio

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

python main.py
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## Run on Linux/macOS

```bash
git clone https://github.com/msarsari/youtube2audio.git
cd youtube2audio

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

python main.py
```

## Notes

YouTube changes frequently. Keeping yt-dlp current is the first troubleshooting step when extraction stops working:

```bash
python -m pip install -U yt-dlp
```

Use the application only for content you are permitted to download or process.

## Development

Run tests with:

```bash
python -m unittest discover -s tests -v
```

The current modernization keeps the PyQt5 interface intentionally stable. Planned follow-up work can add quality selection, per-item progress, cancellation, saved preferences, browser cookies, and a standalone Windows executable.
