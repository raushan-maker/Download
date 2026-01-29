from flask import Flask, render_template, request, send_file, jsonify, redirect
import yt_dlp
import os
import re
import requests
from urllib.parse import urlparse
from downloader_utils import resolve_download_path
from ffmpeg_utils import ensure_ffmpeg, BIN_DIR
from spotify import get_track_info, get_track_metadata, download_from_youtube  # ✅ Spotify integration

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

ensure_ffmpeg()

API_TOKEN = os.environ.get("NUBCODER_TOKEN", "CIMzU2EK0N")
API_BASE_URL = "http://api.nubcoder.com"
API_FORMAT_ID = "api-direct"


def is_spotify_url(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    return 'open.spotify.com' in lowered or lowered.startswith('spotify:')

@app.route('/')
def index():
    return render_template('index.html')


def format_size(bytes_val):
    if not bytes_val: return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} TB"


def sanitize_filename(name: str) -> str:
    if not name:
        return "Video"
    cleaned = re.sub(r'[^A-Za-z0-9\-_. ]+', ' ', name).strip()
    return cleaned or "Video"


def fetch_api_data(video_url: str):
    try:
        response = requests.get(
            f"{API_BASE_URL}/info",
            params={'token': API_TOKEN, 'q': video_url},
            timeout=20
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get('url'):
            return data
    except Exception as exc:
        print(f"API fallback failed: {exc}")
    return None


def download_via_api(api_data: dict):
    if not api_data:
        return None
    download_url = api_data.get('url')
    if not download_url:
        return None

    title = sanitize_filename(api_data.get('title') or api_data.get('video_id'))
    parsed = urlparse(download_url)
    ext = os.path.splitext(parsed.path)[1] or '.mp4'
    filename = f"{title}(-by Alex){ext}"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    headers = api_data.get('headers') or {}

    try:
        with requests.get(download_url, stream=True, headers=headers, timeout=60) as response:
            response.raise_for_status()
            with open(filepath, 'wb') as fh:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
    except Exception as exc:
        print(f"API download failed: {exc}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return None

    return filepath


@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    if not url:
        return "URL is required!", 400
    
    if is_spotify_url(url):
        metadata = get_track_metadata(url)
        if not metadata:
            return "Failed to fetch Spotify track metadata", 500
        track_path = download_from_youtube(metadata['query'])
        if not track_path or not os.path.exists(track_path):
            return "Failed to download Spotify track", 500
        return send_file(track_path, as_attachment=True)

    selected_format = request.form.get('format', 'best')

    if selected_format == API_FORMAT_ID:
        api_data = fetch_api_data(url)
        if not api_data:
            return "API fallback failed to fetch video", 500
        filepath = download_via_api(api_data)
        if not filepath or not os.path.exists(filepath):
            return "API fallback failed to download video", 500
        return send_file(filepath, as_attachment=True)
    
    # Use video title in filename with "(-by Alex)" suffix
    output_path = os.path.join(DOWNLOAD_FOLDER, '%(title)s(-by Alex).%(ext)s')

    ydl_opts = {
        'outtmpl': output_path,
        'noplaylist': True,
        'writethumbnail': True,       # ✅ Download thumbnail
        'postprocessors': [{
            'key': 'EmbedThumbnail',  # ✅ Embed thumbnail in file
        }],
        'overwrites': True,           # Overwrite if file exists
        'ffmpeg_location': str(BIN_DIR),
    }

    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    # Handle format selection
    if selected_format == 'best':
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    else:
        # User selected a specific format ID.
        # Attempt to merge with best audio if possible (common useful behavior for YouTube video-only streams),
        # but fallback to just the selected format if merging fails or isn't needed.
        ydl_opts['format'] = f"{selected_format}+bestaudio/{selected_format}"

    def run_download(options):
        # Execute yt-dlp and resolve the final output path, even after post-processing.
        with yt_dlp.YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filepath = resolve_download_path(info_dict, ydl, output_path)
            if not filepath or not os.path.exists(filepath):
                raise FileNotFoundError(f"Download finished but file missing: {filepath or 'unknown'}")
            return filepath

    try:
        filepath = run_download(ydl_opts)
    except yt_dlp.utils.DownloadError as e:
        # If download fails with cookies (e.g., "Requested format is not available" or 403),
        # try again WITHOUT cookies as a fallback.
        if ydl_opts.pop('cookiefile', None):
            print(f"Download failed with cookies, retrying without... Error: {e}")
            try:
                filepath = run_download(ydl_opts)
            except yt_dlp.utils.DownloadError:
                api_data = fetch_api_data(url)
                if api_data:
                    filepath = download_via_api(api_data)
                    if filepath and os.path.exists(filepath):
                        return send_file(filepath, as_attachment=True)
                raise
            except FileNotFoundError as missing:
                api_data = fetch_api_data(url)
                if api_data:
                    filepath = download_via_api(api_data)
                    if filepath and os.path.exists(filepath):
                        return send_file(filepath, as_attachment=True)
                return str(missing), 500
        else:
            api_data = fetch_api_data(url)
            if api_data:
                filepath = download_via_api(api_data)
                if filepath and os.path.exists(filepath):
                    return send_file(filepath, as_attachment=True)
            raise e
    except FileNotFoundError as missing:
        api_data = fetch_api_data(url)
        if api_data:
            filepath = download_via_api(api_data)
            if filepath and os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
        return str(missing), 500

    return send_file(filepath, as_attachment=True)

def clean_error_message(error_str):
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', error_str)

@app.route('/video_info', methods=['POST'])
def video_info():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    if is_spotify_url(url):
        metadata = get_track_metadata(url)
        if not metadata:
            return jsonify({'error': 'Failed to fetch Spotify metadata'}), 500
        return jsonify({
            'title': metadata['title'],
            'thumbnail': metadata.get('thumbnail'),
            'formats': [],
            'isSpotify': True
        })

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        # 'forcejson': True, # Removed as it can cause issues in library usage
        'noplaylist': True,
    }

    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    info = None
    last_error = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        last_error = exc
        if 'cookiefile' in ydl_opts:
            try:
                opts_no_cookie = dict(ydl_opts)
                opts_no_cookie.pop('cookiefile', None)
                with yt_dlp.YoutubeDL(opts_no_cookie) as ydl_no_cookie:
                    info = ydl_no_cookie.extract_info(url, download=False)
            except Exception as exc_no_cookie:
                last_error = exc_no_cookie

    if info:
        def get_fmt_size(fmt):
            size = fmt.get('filesize') or fmt.get('filesize_approx')
            return format_size(size)

        formats_list = [{'id': 'best', 'label': 'Best Quality (Auto)'}]

        for fmt in info.get('formats', []):
            fid = fmt.get('format_id')
            ext = fmt.get('ext')
            w = fmt.get('width')
            h = fmt.get('height')

            if w and h:
                res = f"{w}x{h}"
            elif fmt.get('vcodec') == 'none':
                res = "audio only"
            elif fmt.get('resolution'):
                res = fmt.get('resolution')
            else:
                res = "unknown"

            size_str = get_fmt_size(fmt)
            note = fmt.get('format_note', '')
            tbr = fmt.get('tbr')

            label_parts = [fid, ext, res]
            if note:
                label_parts.append(note)
            if tbr:
                label_parts.append(f"{int(tbr)}k")
            label_parts.append(size_str)

            label = " - ".join(str(part) for part in label_parts if part)
            formats_list.append({'id': fid, 'label': label})

        if len(formats_list) <= 1:
            api_data = fetch_api_data(url)
            if api_data:
                formats_list.append({'id': API_FORMAT_ID, 'label': 'Direct MP4 (API fallback)'})

        return jsonify({
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'formats': formats_list
        })

    api_data = fetch_api_data(url)
    if api_data:
        return jsonify({
            'title': api_data.get('title'),
            'thumbnail': api_data.get('thumbnail'),
            'formats': [{'id': API_FORMAT_ID, 'label': 'Direct MP4 (API fallback)'}],
            'apiFallback': True
        })

    error_msg = clean_error_message(str(last_error)) if last_error else 'Unknown error'
    print(f"Error extracting info: {error_msg}")
    return jsonify({'error': error_msg}), 500

@app.route('/spotify', methods=['POST'])
def spotify_download():
    spotify_url = request.form.get('spotify_url')
    if not spotify_url:
        return "No Spotify URL provided", 400

    query = get_track_info(spotify_url)
    if query:
        filepath = download_from_youtube(query)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return render_template("index.html", message="❌ Downloaded file not found.")
    else:
        return render_template("index.html", message="❌ Failed to download Spotify song.")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
