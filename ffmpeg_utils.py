import os
import stat
import tarfile
import shutil
import tempfile
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin"
IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    FFMPEG_BINARY = "ffmpeg.exe"
    FFPROBE_BINARY = "ffprobe.exe"
    # Windows builds are much larger; instruct manual install if needed.
    FFMPEG_URL = None
else:
    FFMPEG_BINARY = "ffmpeg"
    FFPROBE_BINARY = "ffprobe"
    FFMPEG_URL = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

FFMPEG_PATH = BIN_DIR / FFMPEG_BINARY
FFPROBE_PATH = BIN_DIR / FFPROBE_BINARY


def _download_ffmpeg(archive_path: Path) -> None:
    if not FFMPEG_URL:
        raise RuntimeError("Automatic ffmpeg setup not supported on this platform")

    response = requests.get(FFMPEG_URL, stream=True, timeout=60)
    response.raise_for_status()

    with archive_path.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=1024 * 512):
            if chunk:
                fh.write(chunk)


def _extract_and_install(archive_path: Path) -> None:
    with tarfile.open(archive_path, mode="r:xz") as tar:
        with tempfile.TemporaryDirectory(dir=BASE_DIR) as tmp_dir:
            tar.extractall(tmp_dir)
            tmp_path = Path(tmp_dir)
            candidates = [d for d in tmp_path.iterdir() if d.is_dir() and d.name.startswith("ffmpeg-")]
            if not candidates:
                raise RuntimeError("Failed to locate extracted ffmpeg directory")
            source_dir = candidates[0]
            ffmpeg_src = source_dir / FFMPEG_BINARY
            ffprobe_src = source_dir / FFPROBE_BINARY
            if not ffmpeg_src.exists() or not ffprobe_src.exists():
                raise RuntimeError("Extracted ffmpeg binaries not found")
            BIN_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(ffmpeg_src), FFMPEG_PATH)
            shutil.move(str(ffprobe_src), FFPROBE_PATH)

    archive_path.unlink(missing_ok=True)

    os.chmod(FFMPEG_PATH, stat.S_IRWXU)
    os.chmod(FFPROBE_PATH, stat.S_IRWXU)


def ensure_ffmpeg() -> None:
    if FFMPEG_PATH.exists() and FFPROBE_PATH.exists():
        os.environ.setdefault("PATH", "")
        if str(BIN_DIR) not in os.environ["PATH"]:
            os.environ["PATH"] = f"{BIN_DIR}{os.pathsep}" + os.environ["PATH"]
        return

    if IS_WINDOWS:
        # Windows deployments should bundle ffmpeg manually; skip auto-install.
        return

    archive_path = BASE_DIR / "ffmpeg.tar.xz"

    _download_ffmpeg(archive_path)
    _extract_and_install(archive_path)

    os.environ.setdefault("PATH", "")
    if str(BIN_DIR) not in os.environ["PATH"]:
        os.environ["PATH"] = f"{BIN_DIR}{os.pathsep}" + os.environ["PATH"]
