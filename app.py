from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
import re
import requests
import threading
import uuid
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

import yt_dlp

from downloader_utils import resolve_download_path
from ffmpeg_utils import ensure_ffmpeg, BIN_DIR
from spotify import get_track_info, get_track_metadata, download_from_youtube

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

ensure_ffmpeg()

API_TOKEN = os.environ.get("NUBCODER_TOKEN", "CIMzU2EK0N")
API_BASE_URL = "http://api.nubcoder.com"
API_FORMAT_ID = "api-direct"

_download_jobs: Dict[str, Dict[str, Any]] = {}
_download_lock = threading.Lock()


def clamp_progress(value: Optional[float]) -> Optional[int]:
    if value is None:
        return None
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return None


def create_job() -> str:
    job_id = uuid.uuid4().hex
    with _download_lock:
        _download_jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "message": "Queued",
            "filepath": None,
            "error": None,
            "requested_format": None,
            "source_url": None,
        }
    return job_id


def update_job(job_id: str, **fields: Any) -> None:
    if not fields:
        return
    with _download_lock:
        job = _download_jobs.get(job_id)
        if not job:
            return
        job.update(fields)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _download_lock:
        job = _download_jobs.get(job_id)
        if not job:
            return None
        return dict(job)


def report_job_progress(
    job_id: Optional[str],
    *,
    progress: Optional[float] = None,
    message: Optional[str] = None,
    status: Optional[str] = None,
) -> None:
    if not job_id:
        return
    updates: Dict[str, Any] = {}
    percent = clamp_progress(progress)
    if percent is not None:
        updates["progress"] = percent
    if message is not None:
        updates["message"] = message
    if status is not None:
        updates["status"] = status
    if updates:
        update_job(job_id, **updates)


def make_progress_hook(job_id: str) -> Callable[[Dict[str, Any]], None]:
    def _hook(data: Dict[str, Any]) -> None:
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes") or 0
            percent = None
            if total:
                try:
                    percent = (downloaded / float(total)) * 100
                except (TypeError, ValueError, ZeroDivisionError):
                    percent = None
            parts = ["Downloading"]
            percent_text = data.get("_percent_str")
            eta_text = data.get("_eta_str")
            if percent_text:
                parts.append(percent_text.strip())
            if eta_text:
                parts.append(f"ETA {eta_text.strip()}")
            report_job_progress(
                job_id,
                progress=percent or 1,
                message=" | ".join(parts),
                status="downloading",
            )
        elif status == "finished":
            report_job_progress(job_id, progress=96, message="Post-processing...", status="processing")
        elif status == "error":
            error_msg = data.get("filename") or "Download error"
            report_job_progress(job_id, progress=0, message=error_msg, status="error")

    return _hook


def is_spotify_url(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    return "open.spotify.com" in lowered or lowered.startswith("spotify:")


@app.route("/")
def index():
    return render_template("index.html")


def format_size(bytes_val):
    if not bytes_val:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} TB"


def sanitize_filename(name: str) -> str:
    if not name:
        return "Video"
    cleaned = re.sub(r"[^A-Za-z0-9\-_. ]+", " ", name).strip()
    return cleaned or "Video"


def fetch_api_data(video_url: str):
    try:
        response = requests.get(
            f"{API_BASE_URL}/info",
            params={"token": API_TOKEN, "q": video_url},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("url"):
            return data
    except Exception as exc:
        print(f"API fallback failed: {exc}")
    return None


def download_via_api(
    api_data: dict,
    progress_callback: Optional[Callable[[Optional[float], str], None]] = None,
):
    if not api_data:
        return None
    download_url = api_data.get("url")
    if not download_url:
        return None

    title = sanitize_filename(api_data.get("title") or api_data.get("video_id"))
    parsed_ext = os.path.splitext(urlparse(download_url).path)[1] or ".mp4"
    filename = f"{title}(-by Alex){parsed_ext}"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    headers = dict(api_data.get("headers") or {})
    headers.setdefault(
        "User-Agent",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
    )
    headers.setdefault("Accept", "*/*")
    headers.setdefault("Connection", "keep-alive")
    referer = api_data.get("referer") or api_data.get("origin") or api_data.get("page")
    if referer:
        headers.setdefault("Referer", referer)

    try:
        with requests.get(download_url, stream=True, headers=headers, timeout=60) as response:
            response.raise_for_status()
            total_bytes = int(response.headers.get("content-length") or 0)
            downloaded = 0
            with open(filepath, "wb") as fh:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        percent = None
                        if total_bytes:
                            try:
                                percent = (downloaded / float(total_bytes)) * 100
                            except (TypeError, ValueError, ZeroDivisionError):
                                percent = None
                        size_msg = f"Downloading via fallback {format_size(downloaded)}"
                        if total_bytes:
                            size_msg += f" of {format_size(total_bytes)}"
                        progress_callback(percent, size_msg)
    except Exception as exc:
        print(f"API download failed: {exc}")
        if progress_callback:
            progress_callback(0, f"Fallback error: {exc}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return None

    if progress_callback:
        progress_callback(100, "Download ready")
    return filepath


def perform_download(url: str, selected_format: str, job_id: Optional[str] = None) -> str:
    if not url:
        raise ValueError("URL is required")

    if is_spotify_url(url):
        report_job_progress(job_id, progress=1, message="Fetching Spotify metadata...", status="starting")
        metadata = get_track_metadata(url)
        if not metadata:
            raise RuntimeError("Failed to fetch Spotify track metadata")
        hook = make_progress_hook(job_id) if job_id else None
        track_path = download_from_youtube(metadata["query"], progress_hook=hook)
        if not track_path or not os.path.exists(track_path):
            raise RuntimeError("Failed to download Spotify track")
        report_job_progress(job_id, progress=100, message="Spotify download ready", status="completed")
        return track_path

    if selected_format == API_FORMAT_ID:
        report_job_progress(job_id, progress=5, message="Using fallback downloader...", status="downloading")
        api_data = fetch_api_data(url)
        if not api_data:
            raise RuntimeError("API fallback failed to fetch video")
        progress_cb = (
            (lambda pct, msg: report_job_progress(job_id, progress=pct, message=msg, status="downloading"))
            if job_id
            else None
        )
        filepath = download_via_api(api_data, progress_callback=progress_cb)
        if not filepath or not os.path.exists(filepath):
            raise RuntimeError("API fallback failed to download video")
        report_job_progress(job_id, progress=100, message="Download ready", status="completed")
        return filepath

    output_path = os.path.join(DOWNLOAD_FOLDER, "%(title)s(-by Alex).%(ext)s")
    ydl_opts: Dict[str, Any] = {
        "outtmpl": output_path,
        "noplaylist": True,
        "writethumbnail": True,
        "postprocessors": [{"key": "EmbedThumbnail"}],
        "overwrites": True,
        "ffmpeg_location": str(BIN_DIR),
    }

    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"

    if selected_format == "best":
        ydl_opts["format"] = "bestvideo+bestaudio/best"
    else:
        ydl_opts["format"] = f"{selected_format}+bestaudio/{selected_format}"

    if job_id:
        ydl_opts["progress_hooks"] = [make_progress_hook(job_id)]
        report_job_progress(job_id, progress=2, message="Starting download...", status="downloading")

    def run_download(options: Dict[str, Any]) -> str:
        with yt_dlp.YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filepath_local = resolve_download_path(info_dict, ydl, output_path)
            if not filepath_local or not os.path.exists(filepath_local):
                raise FileNotFoundError(f"Download finished but file missing: {filepath_local or 'unknown'}")
            return filepath_local

    try:
        filepath = run_download(dict(ydl_opts))
    except yt_dlp.utils.DownloadError as error:
        cookiefile = ydl_opts.pop("cookiefile", None)
        if cookiefile:
            print(f"Download failed with cookies, retrying without... Error: {error}")
            try:
                filepath = run_download(dict(ydl_opts))
            except yt_dlp.utils.DownloadError:
                api_data = fetch_api_data(url)
                if api_data:
                    report_job_progress(job_id, progress=10, message="Switching to fallback...", status="downloading")
                    progress_cb = (
                        (lambda pct, msg: report_job_progress(job_id, progress=pct, message=msg, status="downloading"))
                        if job_id
                        else None
                    )
                    filepath = download_via_api(api_data, progress_callback=progress_cb)
                    if filepath and os.path.exists(filepath):
                        report_job_progress(job_id, progress=100, message="Download ready", status="completed")
                        return filepath
                raise
            except FileNotFoundError as missing:
                api_data = fetch_api_data(url)
                if api_data:
                    report_job_progress(job_id, progress=10, message="Switching to fallback...", status="downloading")
                    progress_cb = (
                        (lambda pct, msg: report_job_progress(job_id, progress=pct, message=msg, status="downloading"))
                        if job_id
                        else None
                    )
                    filepath = download_via_api(api_data, progress_callback=progress_cb)
                    if filepath and os.path.exists(filepath):
                        report_job_progress(job_id, progress=100, message="Download ready", status="completed")
                        return filepath
                raise RuntimeError(str(missing))
        else:
            api_data = fetch_api_data(url)
            if api_data:
                report_job_progress(job_id, progress=10, message="Switching to fallback...", status="downloading")
                progress_cb = (
                    (lambda pct, msg: report_job_progress(job_id, progress=pct, message=msg, status="downloading"))
                    if job_id
                    else None
                )
                filepath = download_via_api(api_data, progress_callback=progress_cb)
                if filepath and os.path.exists(filepath):
                    report_job_progress(job_id, progress=100, message="Download ready", status="completed")
                    return filepath
            raise error
    except FileNotFoundError as missing:
        api_data = fetch_api_data(url)
        if api_data:
            report_job_progress(job_id, progress=10, message="Switching to fallback...", status="downloading")
            progress_cb = (
                (lambda pct, msg: report_job_progress(job_id, progress=pct, message=msg, status="downloading"))
                if job_id
                else None
            )
            filepath = download_via_api(api_data, progress_callback=progress_cb)
            if filepath and os.path.exists(filepath):
                report_job_progress(job_id, progress=100, message="Download ready", status="completed")
                return filepath
        raise RuntimeError(str(missing))

    report_job_progress(job_id, progress=100, message="Download ready", status="completed")
    return filepath


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    if not url:
        return "URL is required!", 400

    selected_format = request.form.get("format", "best")

    try:
        filepath = perform_download(url, selected_format, job_id=None)
    except yt_dlp.utils.DownloadError as err:
        return str(err), 500
    except Exception as exc:
        return str(exc), 500

    if not filepath or not os.path.exists(filepath):
        return "Download finished but file missing", 500

    return send_file(filepath, as_attachment=True)


def process_download_job(job_id: str, url: str, selected_format: str) -> None:
    try:
        filepath = perform_download(url, selected_format, job_id=job_id)
        if filepath and os.path.exists(filepath):
            update_job(job_id, filepath=filepath)
            report_job_progress(job_id, progress=100, message="Download ready", status="completed")
        else:
            raise RuntimeError("Download finished but file missing")
    except Exception as exc:
        message = str(exc) or "Download failed"
        report_job_progress(job_id, progress=0, message=message, status="error")
        update_job(job_id, error=message)


@app.route("/start_download", methods=["POST"])
def start_download():
    url = (request.form.get("url") or "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    selected_format = request.form.get("format", "best")
    job_id = create_job()
    update_job(job_id, source_url=url, requested_format=selected_format)
    report_job_progress(job_id, progress=1, message="Preparing download...", status="starting")

    worker = threading.Thread(target=process_download_job, args=(job_id, url, selected_format), daemon=True)
    worker.start()

    return jsonify({"jobId": job_id})


@app.route("/download_status/<job_id>")
def download_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Invalid job id"}), 404

    response = {
        "status": job.get("status", "pending"),
        "progress": job.get("progress", 0),
        "message": job.get("message") or "",
    }

    if job.get("error"):
        response["error"] = job["error"]

    if job.get("status") == "completed" and job.get("filepath"):
        response["downloadUrl"] = url_for("download_file", job_id=job_id)

    return jsonify(response)


@app.route("/download_file/<job_id>")
def download_file(job_id: str):
    job = get_job(job_id)
    if not job:
        return "Invalid job id", 404

    if job.get("status") != "completed":
        return "Download in progress", 409

    filepath = job.get("filepath")
    if not filepath or not os.path.exists(filepath):
        return "File not found", 404

    return send_file(filepath, as_attachment=True)


def clean_error_message(error_str):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", error_str)


@app.route("/video_info", methods=["POST"])
def video_info():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if is_spotify_url(url):
        metadata = get_track_metadata(url)
        if not metadata:
            return jsonify({"error": "Failed to fetch Spotify metadata"}), 500
        return jsonify(
            {
                "title": metadata["title"],
                "thumbnail": metadata.get("thumbnail"),
                "formats": [],
                "isSpotify": True,
            }
        )

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
    }

    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"

    info = None
    last_error = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        last_error = exc
        if "cookiefile" in ydl_opts:
            try:
                opts_no_cookie = dict(ydl_opts)
                opts_no_cookie.pop("cookiefile", None)
                with yt_dlp.YoutubeDL(opts_no_cookie) as ydl_no_cookie:
                    info = ydl_no_cookie.extract_info(url, download=False)
            except Exception as exc_no_cookie:
                last_error = exc_no_cookie

    if info:
        def get_fmt_size(fmt):
            size = fmt.get("filesize") or fmt.get("filesize_approx")
            return format_size(size)

        formats_list = [{"id": "best", "label": "Best Quality (Auto)"}]

        for fmt in info.get("formats", []):
            fid = fmt.get("format_id")
            ext = fmt.get("ext")
            w = fmt.get("width")
            h = fmt.get("height")

            if w and h:
                res = f"{w}x{h}"
            elif fmt.get("vcodec") == "none":
                res = "audio only"
            elif fmt.get("resolution"):
                res = fmt.get("resolution")
            else:
                res = "unknown"

            size_str = get_fmt_size(fmt)
            note = fmt.get("format_note", "")
            tbr = fmt.get("tbr")

            label_parts = [fid, ext, res]
            if note:
                label_parts.append(note)
            if tbr:
                label_parts.append(f"{int(tbr)}k")
            label_parts.append(size_str)

            label = " - ".join(str(part) for part in label_parts if part)
            formats_list.append({"id": fid, "label": label})

        if len(formats_list) <= 1:
            api_data = fetch_api_data(url)
            if api_data:
                formats_list.append({"id": API_FORMAT_ID, "label": "Direct MP4 (API fallback)"})

        return jsonify(
            {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "formats": formats_list,
            }
        )

    api_data = fetch_api_data(url)
    if api_data:
        return jsonify(
            {
                "title": api_data.get("title"),
                "thumbnail": api_data.get("thumbnail"),
                "formats": [{"id": API_FORMAT_ID, "label": "Direct MP4 (API fallback)"}],
                "apiFallback": True,
            }
        )

    error_msg = clean_error_message(str(last_error)) if last_error else "Unknown error"
    print(f"Error extracting info: {error_msg}")
    return jsonify({"error": error_msg}), 500


@app.route("/spotify", methods=["POST"])
def spotify_download():
    spotify_url = request.form.get("spotify_url")
    if not spotify_url:
        return "No Spotify URL provided", 400

    query = get_track_info(spotify_url)
    if query:
        filepath = download_from_youtube(query)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        return render_template("index.html", message="Failed to locate Spotify download")
    return render_template("index.html", message="Failed to download Spotify song")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
