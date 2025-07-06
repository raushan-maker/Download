<h1 align="center">
  🎥 YT-DLP Video Downloader 🔻
</h1>

<p align="center">
  <img src="https://img.shields.io/github/license/your-username/yt-dlp-downloader?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Flask-%20Python-blue?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/yt--dlp-Supported-orange?style=for-the-badge" />
</p>

<p align="center">
  <img src="https://media.giphy.com/media/jt7bAtEijhurm/giphy.gif" width="300" alt="Downloading..." />
</p>

---

## 🌐 Live Demo

[![Live on Render](https://img.shields.io/badge/View%20App-Launch-green?style=for-the-badge&logo=render)](https://downloader-nuck.onrender.com/)

---

## 🧠 About

> A sleek, modern downloader app that lets users download videos from YouTube, TikTok, Vimeo, Instagram, Facebook, Twitter and more using the powerful `yt-dlp`.  
> Built with ❤️ using Flask, HTML, CSS, JS — and has preview thumbnail + title before download.

---

## 🔐 YouTube Requires Cookies.txt

Due to recent YouTube restrictions, **cloud-hosted apps like Render must use cookies** to download YouTube videos.

✅ This app supports `cookies.txt`, so:
- Works perfectly for YouTube (even age-restricted/private)
- Still works for all **other websites** without cookies

### 📥 How to Export Cookies
1. Install [Get cookies.txt Extension](https://chrome.google.com/webstore/detail/get-cookiestxt/eeeekgogddiflieebojnegilcmlnnbjl)
2. Visit https://youtube.com
3. Click the extension → Download cookies
4. Save as `cookies.txt` and place it in your project root

---

## ✨ Features

- 🎥 Download videos from 1000+ platforms using yt-dlp
- 🔍 Auto-preview: shows video title + thumbnail before download
- 🎨 Stylish full-screen video background UI
- 💾 Automatically picks best quality
- ⚡ Supports Render, Replit, localhost, VPS
- 🚀 Lightweight, mobile-friendly

---

## 📸 Preview

| 🎯 Enter URL | 🔍 Video Info | 📥 Download Ready |
|-------------|---------------|-------------------|
| ![](https://i.imgur.com/PASTED_INPUT_IMG.png) | ![](https://i.imgur.com/PASTED_INFO_IMG.png) | ![](https://i.imgur.com/PASTED_SUCCESS_IMG.png) |

> *(Replace with real screenshots or demo GIF)*

---

## 📁 Folder Structure

```
yt_dlp_downloader/
├── app.py
├── cookies.txt          # ← optional but required for YouTube
├── static/
│   ├── style.css
│   └── bg.mp4
├── templates/
│   └── index.html
├── downloads/
└── requirements.txt
```

---

## 🚀 Getting Started

### 🧩 Requirements
- Python 3.10+
- Flask
- yt-dlp

### 📦 Install Dependencies
```bash
pip install -r requirements.txt
```

### ▶️ Run Locally
```bash
python app.py
```

Then go to: `http://127.0.0.1:5000`

---

## 🌐 Deployment

✅ Works on:
- [Render.com](https://render.com)
- [Replit.com](https://replit.com)
- VPS / localhost

### ⚠️ For Render / Cloud Hosts:
In `app.py`, make sure:
```python
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=True)
```

---

## 🌍 Supported Platforms

> Thanks to yt-dlp, this supports 1000+ platforms:

- ✅ YouTube (requires `cookies.txt`)
- ✅ TikTok
- ✅ Vimeo
- ✅ Facebook
- ✅ Instagram
- ✅ Twitter (X)
- ✅ SoundCloud
- ✅ Reddit
- ✅ and many more...

👉 Full list: [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## 🛡️ Legal Note

> This tool is for **educational & personal use only**. Downloading copyrighted content may violate local laws.

---

## 🧠 Tech Stack

- 🐍 Python + Flask
- 📺 yt-dlp
- 🌐 HTML + CSS + JS
- 🚀 Hosted on Render

---

## 👨‍💻 Author

> Made with 💖 by [Rohit Kumar](https://github.com/rohitt99)

[![Follow](https://img.shields.io/badge/Follow%20Me-GitHub-black?style=for-the-badge&logo=github)](https://github.com/rohitt99)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE)
