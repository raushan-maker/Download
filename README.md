<h1 align="center" style="font-size:3rem; color:#00ffc8; text-shadow: 0 0 15px #00ffc8, 0 0 30px #00ffc8;">
  🔥 Ultimate Video Downloader 💎
</h1><p align="center">
  <img src="https://img.shields.io/github/license/rohitt99/yt-dlp-downloader?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Powered%20By-Flask%20%26%20Python-blue?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/YT--DLP-Enabled-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Spotify-Supported-green?style=for-the-badge&logo=spotify" />
</p><p align="center">
  <img src="https://media.giphy.com/media/jt7bAtEijhurm/giphy.gif" width="350" alt="Downloading..." />
</p>
---

🚀 Live Demo




---

🧠 About the Project

> Universal Video & Music Downloader — built with yt-dlp, Flask, and 🔥 modern web technologies. Supports YouTube, Spotify, TikTok, Instagram, Twitter, Facebook, Vimeo, and more.

🎧 New: Spotify integration to download tracks via YouTube!




---

🔐 YouTube Cookie Support

Due to recent changes, YouTube downloads may require login cookies for full functionality.

✅ This app supports cookies.txt, so you can:

Download age-restricted, private, and login-only YouTube content

Still use all other platforms without cookies


📥 Export Cookies Guide

1. Install Get cookies.txt Extension


2. Open YouTube in your browser


3. Click the extension → Export


4. Save it as cookies.txt in the project root




---

✨ Features

🎞️ Download videos from 1000+ websites

🎧 Spotify Song Downloader via YouTube Search

🔍 Auto video preview (title + thumbnail)

🎬 Format selector (MP4 1080p, 720p, 480p, best)

👥 Google login (user tracking, stats, dashboard)

📊 Admin Panel (downloads, users, stats)

🌐 Multilingual UI via auto browser detection

📲 Installable PWA version (mobile app-like)

🌈 Beautiful animated UI + Dark/Light mode toggle

🔐 Cookie support for YouTube downloads

☁️ Render, VPS & Replit deployment supported



---

🖼️ Screenshots

🎯 Enter URL	🔍 Preview	📥 Download

		


> (Replace above with real screenshots!)




---

📂 Folder Structure

yt_dlp_downloader/
├── app.py                   # Flask backend
├── spotify.py               # Spotify downloader logic
├── requirements.txt         # Python dependencies
├── cookies.txt              # (optional) YouTube login cookies
├── static/
│   ├── bg.mp4               # Background video
│   └── logo.png             # Favicon/logo
├── templates/
│   └── index.html           # Main UI
├── downloads/               # Saved videos/mp3s
├── manifest.json            # For PWA install support
├── service-worker.js        # PWA offline caching
└── README.md


---

⚙️ Installation

1️⃣ Install Dependencies

pip install -r requirements.txt

2️⃣ Run Locally

python app.py

Then open: http://127.0.0.1:5000


---

🌐 Deploy Anywhere

✅ Supported on:

Render.com (free hosting)

Replit.com

VPS (Ubuntu, Python3, etc)

Localhost


> 📌 Ensure your app.py ends with:



port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=True)


---

💻 Supported Platforms

✅ YouTube (with cookies.txt)

✅ TikTok

✅ Vimeo

✅ Facebook

✅ Instagram

✅ Twitter (X)

✅ Reddit

✅ SoundCloud

✅ Spotify (via YouTube)

✅ 1000+ others via yt-dlp


🔗 Full supported sites list


---

🛡️ Disclaimer

> 🚨 This project is for educational & personal use only.

Downloading copyrighted content is against YouTube's TOS and may be illegal in your country. Use responsibly.




---

🧰 Tech Stack

🐍 Python 3.10+

⚙️ Flask

📺 yt-dlp

🌍 HTML, CSS, JS

📲 PWA + Manifest + Service Worker



---

🧑‍🚀 Author

Made with 💖 by Rohit Kumar




---

📄 License

Released under the MIT License

