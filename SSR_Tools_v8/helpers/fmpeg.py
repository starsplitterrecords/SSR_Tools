"""
FFmpeg binary loader.

Ensures ffmpeg/ffprobe are available on PATH by adding local bin folder.
"""

import os
import sys
from pathlib import Path


def add_ffmpeg_to_path():
    """Locate ffmpeg.exe in 00_helpers/bin and prepend to PATH."""
    base = Path(__file__).resolve().parent
    bin_dir = base / "bin"

    if not bin_dir.exists():
        return  # No local ffmpeg available

    bin_str = str(bin_dir)

    if bin_str not in os.environ["PATH"]:
        os.environ["PATH"] = bin_str + os.pathsep + os.environ["PATH"]
