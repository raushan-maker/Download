from flask import Flask, render_template, request, send_file, jsonify, redirect
import yt_dlp
import os
from downloader_utils import resolve_download_path
from spotify import get_track_info, get_track_metadata, download_from_youtube  # ✅ Spotify integration

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


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
            except FileNotFoundError as missing:
                return str(missing), 500
        else:
            raise e
    except FileNotFoundError as missing:
        return str(missing), 500

    return send_file(filepath, as_attachment=True)

import re

# ... existing code ...

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

    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            # 'forcejson': True, # Removed as it can cause issues in library usage
            'noplaylist': True,
        }
        
        # Only add cookiefile if it exists
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception:
                # Retry without cookies if first attempt fails (sometimes cookies expire)
                if 'cookiefile' in ydl_opts:
                    del ydl_opts['cookiefile']
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(url, download=False)
                else:
                    raise

            formats_list = []
            extractor = info.get('extractor_key')
            
            # Helper to get size string
            def get_fmt_size(f):
                size = f.get('filesize') or f.get('filesize_approx')
                return format_size(size)

            # Always list all formats like -F for maximum control
            formats_list.append({'id': 'best', 'label': 'Best Quality (Auto)'})
            
            # Sort formats to make it easier to read (optional but helpful)
            # We iterate through the raw formats list provided by yt-dlp
            for f in info.get('formats', []):
                fid = f.get('format_id')
                ext = f.get('ext')
                w = f.get('width')
                h = f.get('height')
                
                # Construct resolution string
                if w and h:
                    res = f"{w}x{h}"
                elif f.get('vcodec') == 'none':
                    res = "audio only"
                elif f.get('resolution'):
                    res = f.get('resolution')
                else:
                    res = "unknown"
                
                size_str = get_fmt_size(f)
                note = f.get('format_note', '')
                tbr = f.get('tbr') # Bitrate in kbit/s can be useful too
                
                # Construct a label similar to yt-dlp -F output
                # ID - EXT - RESOLUTION - NOTE - SIZE
                label_parts = [fid, ext, res]
                if note: label_parts.append(note)
                if tbr: label_parts.append(f"{int(tbr)}k")
                label_parts.append(size_str)
                
                label = " - ".join(str(p) for p in label_parts)
                formats_list.append({'id': fid, 'label': label})

            # Check for requested formats (video+audio combinations mostly for DASH)
            # Note: yt-dlp 'formats' list usually contains individual streams (video only or audio only) for DASH
            # If the user selects a video-only stream, we might need logic in /download to merge it with best audio
            # But usually 'bestvideo+bestaudio' handles it. 
            # If user explicitely selects an ID, yt-dlp might download just that.
            # However, the user asked for "Give all quality option to select all selective option like -F"
            
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'formats': formats_list
            })
    except Exception as e:
        error_msg = clean_error_message(str(e))
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
