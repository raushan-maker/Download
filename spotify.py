import os
from typing import Optional

import requests
import yt_dlp
from downloader_utils import resolve_download_path
from ffmpeg_utils import ensure_ffmpeg, BIN_DIR
from yt_dlp.utils import DownloadError

ensure_ffmpeg()

OEMBED_ENDPOINT = "https://open.spotify.com/oembed"


def get_track_metadata(spotify_url: str) -> Optional[dict]:
    try:
        response = requests.get(OEMBED_ENDPOINT, params={'url': spotify_url}, timeout=10)
        response.raise_for_status()
        data = response.json()
        title = data.get('title')
        if not title:
            return None
        thumbnail = data.get('thumbnail_url')
        return {
            'query': title,
            'title': title,
            'thumbnail': thumbnail
        }
    except Exception as exc:
        print(f"Error fetching Spotify metadata: {exc}")
        return None


def get_track_info(spotify_url: str) -> Optional[str]:
    metadata = get_track_metadata(spotify_url)
    return metadata['query'] if metadata else None


def download_from_youtube(query: str) -> Optional[str]:
    if not query:
        return None

    print(f"🔍 Searching and downloading: {query}")
    os.makedirs('downloads', exist_ok=True)

    base_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s(-by Alex).%(ext)s',
        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'EmbedThumbnail',
            }
        ],
        'quiet': True,
        'noplaylist': True,
        'overwrites': True,
        'ffmpeg_location': str(BIN_DIR),
    }

    if os.path.exists('cookies.txt'):
        base_opts['cookiefile'] = 'cookies.txt'

    def _run(opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch1:{query}", download=True)
            filepath = resolve_download_path(search_result, ydl, opts.get('outtmpl'))
            if not filepath and 'entries' in search_result:
                entries = search_result.get('entries') or []
                if not entries:
                    return None
                info = entries[0]
                filepath = resolve_download_path(info, ydl, opts.get('outtmpl'))
            if not filepath or not os.path.exists(filepath):
                raise FileNotFoundError(f"Spotify download finished but file missing: {filepath or 'unknown'}")
            return filepath

    try:
        return _run(dict(base_opts))
    except DownloadError as error:
        if base_opts.get('cookiefile'):
            print(f"Spotify download failed with cookies, retrying without... Error: {error}")
            fallback_opts = dict(base_opts)
            fallback_opts.pop('cookiefile', None)
            try:
                return _run(fallback_opts)
            except FileNotFoundError:
                return None
        print(f"Spotify download error: {error}")
        return None
    except FileNotFoundError as missing:
        print(missing)
        return None
