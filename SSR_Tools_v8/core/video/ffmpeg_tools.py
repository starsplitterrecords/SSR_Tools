# 01_core/video/ffmpeg_tools.py
from __future__ import annotations

import subprocess
from pathlib import Path


def ffprobe_duration(path: str | Path) -> float:
    """Return video duration in seconds."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)


def extract_clip(src: str | Path, out: str | Path, start: float, dur: float) -> None:
    """Extract [start, start+dur] from src video."""
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-t", str(dur),
        "-i", str(src),
        "-c", "copy",
        str(out),
    ]
    subprocess.run(cmd, check=True)


def concat_clips(files: list[str], out: str) -> None:
    """Concatenate clips using ffmpeg concat demuxer."""
    list_file = Path(out).with_suffix(".txt")
    with list_file.open("w") as f:
        for path in files:
            f.write(f"file '{path}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        out,
    ]
    subprocess.run(cmd, check=True)


def mux_audio(video: str, audio: str, out: str) -> None:
    """Replace video's audio track with given WAV/MP3."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video),
        "-i", str(audio),
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-shortest",
        out,
    ]
    subprocess.run(cmd, check=True)
