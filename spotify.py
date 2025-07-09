import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# 🔑 Replace with your own Spotify API keys
SPOTIFY_CLIENT_ID = '15ca3d00f07847c39ce955672ed73176'
SPOTIFY_CLIENT_SECRET = '4e836fcd0b3d4bbea37d6672d0c6c689'

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

def get_track_info(spotify_url):
    try:
        track = sp.track(spotify_url)
        title = track['name']
        artist = track['artists'][0]['name']
        return f"{title} - {artist}"
    except Exception as e:
        print("Error fetching track info:", e)
        return None

def download_from_youtube(query):
    print(f"🔍 Searching and downloading: {query}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.download([f"ytsearch:{query}"])
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        filename = ydl.prepare_filename(info['entries'][0])
        final_path = filename.rsplit('.', 1)[0] + '.mp3'
        return final_path
