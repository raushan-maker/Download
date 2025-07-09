<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com/?center=true&vCenter=true&width=700&lines=🚀+Welcome+to+Universal+Video+%26+Spotify+Downloader;Built+with+YT-DLP+%7C+Flask+%7C+Spotipy;Download+from+1000%2B+Platforms+%F0%9F%94%A5"/>
</p>

<h1 align="center">
  <img src="https://media.giphy.com/media/dsKnRuALlWsZG/giphy.gif" width="60"> Universal Video Downloader <img src="https://media.giphy.com/media/dsKnRuALlWsZG/giphy.gif" width="60">
</h1>

<p align="center">
  <img src="https://img.shields.io/github/stars/rohitt99/universal-video-downloader?color=yellow&logo=github&style=for-the-badge"/>
  <img src="https://img.shields.io/github/forks/rohitt99/universal-video-downloader?color=blue&style=for-the-badge"/>
  <img src="https://img.shields.io/github/license/rohitt99/universal-video-downloader?style=for-the-badge&color=green" />
  <img src="https://img.shields.io/badge/Flask-%20Python-blue?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/yt--dlp-Supported-orange?style=for-the-badge" />
</p>
<p align="center">
  <img src="https://media.giphy.com/media/jt7bAtEijhurm/giphy.gif" width="500" />
</p>
---

## 🌐 Live Demo

👉 [Launch App Now](https://downloader-nuck.onrender.com/)

---

## ✨ Features

- 🎥 **Download videos** from YouTube, TikTok, Vimeo, Facebook, Twitter, Instagram, Reddit, and 1000+ sites
- 🧠 **Auto-Preview** (title + thumbnail)
- 📼 **MP4 Format Selector** (1080p, 720p, 480p, etc.)
- 🎧 **Spotify Downloader** using `yt-dlp` + `Spotipy`
- 📊 **Download Stats + Admin Panel**
- 🌍 **Auto Language Detection + i18n ready**
- 🔐 **Google Login Authentication**
- 🖥️ **PWA** (Installable as App)
- 🔥 Full-screen video background with dark/light mode toggle

---

## 🧠 About This Project

> This is a premium-level SaaS-style **Video + Spotify Downloader**, with a stylish UI, dynamic features, Google login, download analytics, and instant format previews — powered by `yt-dlp`, `Flask`, and `Spotipy`. 

---

## 🧾 Folder Structure

```bash
universal-downloader/
├── app.py                   # Flask app core
├── spotify.py              # Spotify downloading logic
├── requirements.txt
├── cookies.txt             # Optional, for YouTube auth
├── downloads/              # Downloaded media files
├── static/
│   ├── bg.mp4              # Background video
│   └── logo.png
├── templates/
│   └── index.html          # UI frontend
├── manifest.json           # PWA support
├── service-worker.js       # PWA offline support
└── README.md               # You're here 🥂
```

---

## ⚙️ Setup Locally

```bash
git clone https://github.com/rohitt99/universal-video-downloader.git
cd universal-video-downloader
pip install -r requirements.txt
python app.py
```

> Open your browser: [http://localhost:5000](http://localhost:5000)

---

## 💽 Cookies for YouTube

YouTube now requires cookies for some videos (age-restricted, region-locked, etc.).

### How To Export Cookies:

1. Install this 👉 [Get Cookies.txt Chrome Extension](https://chrome.google.com/webstore/detail/get-cookiestxt/eeeekgogddiflieebojnegilcmlnnbjl)
2. Go to [YouTube](https://youtube.com)
3. Click the extension → Export → Save as `cookies.txt`
4. Drop it in the root of your project

---

## ☁️ Deployment

Supports:

- ✅ [Render](https://render.com)
- ✅ [Replit](https://replit.com)
- ✅ Localhost
- ✅ VPS

```python
# Required in app.py:
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port, debug=True)
```

---

## 🎧 Spotify Downloader

Spotify songs are fetched via Spotipy → searched & downloaded from YouTube using `yt-dlp`.

Just paste a Spotify track URL and we’ll handle the rest 💫

```bash
POST /spotify
Body: spotify_url=...
```

---

## 🌍 Supported Platforms

> Thanks to yt-dlp, you get support for **over 1000 websites**:

- ✅ YouTube (w/ cookies)
- ✅ TikTok
- ✅ Vimeo
- ✅ Facebook
- ✅ Twitter (X)
- ✅ Instagram
- ✅ Reddit
- ✅ SoundCloud

👉 [Full List Here](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## 🔐 Tech Stack

- 💻 Python 3.10+
- 🧠 Flask + Jinja2
- 🎬 yt-dlp (video/audio downloader)
- 🎧 Spotipy (Spotify API wrapper)
- 🧩 HTML, CSS, JS (Frontend)
- 🧠 PWA + Manifest + Service Worker

---

## 📸 Screenshots

| URL Input | Video Info Preview | Admin Panel |
|----------|---------------------|-------------|
| ![](https://i.imgur.com/PASTED_INPUT_IMG.png) | ![](https://i.imgur.com/PASTED_INFO_IMG.png) | ![](https://i.imgur.com/PASTED_SUCCESS_IMG.png) |

> Replace with your actual screenshots

---

## 👤 Author

> Built by [**Rohit Kumar 🥀**](https://github.com/rohitt99) with 💖

[![GitHub Follow](https://img.shields.io/badge/Follow--me--on--GitHub-black?style=for-the-badge&logo=github)](https://github.com/rohitt99)

---

## 📜 License

Released under [MIT License](LICENSE)

---

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F%20by%20Rohit%20🥀-purple?style=for-the-badge" />
</p>

