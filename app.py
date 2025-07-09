from flask import Flask, render_template, request, send_file, jsonify, redirect
import yt_dlp
import os
import uuid
from spotify import get_track_info, download_from_youtube  # ✅ Spotify integration

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    if not url:
        return "URL is required!", 400

    video_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_FOLDER, f'{video_id}.%(ext)s')

    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'cookiefile': 'cookies.txt'  # ✅ YouTube cookies support
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)

    return send_file(filename, as_attachment=True)

@app.route('/video_info', methods=['POST'])
def video_info():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'forcejson': True,
            'cookiefile': 'cookies.txt'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail')
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
