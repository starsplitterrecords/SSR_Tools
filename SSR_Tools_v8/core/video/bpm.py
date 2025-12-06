# 01_core/video/bpm.py
from __future__ import annotations

import subprocess
import numpy as np
import tempfile
from pathlib import Path


def detect_bpm(audio_path: str | Path) -> float:
    """
    Very rough BPM detector for beat-synced video.

    Uses autocorrelation on downsampled audio peaks.
    Accuracy is not perfect but sufficient for beat grid alignment.
    """

    # Extract mono audio samples using ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(audio_path),
        "-ac", "1",
        "-ar", "11025",
        wav_path,
    ]
    subprocess.run(cmd, check=True)

    import wave

    with wave.open(wav_path, "rb") as w:
        frames = w.readframes(w.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

    # Envelope extraction
    env = np.abs(samples)
    env = env - env.mean()
    env = env / (env.std() + 1e-9)

    corr = np.correlate(env, env, mode="full")[len(env):]
    peaks = np.argsort(corr)[-5:]

    diffs = np.diff(np.sort(peaks))
    if len(diffs) == 0:
        return 120.0  # fallback

    avg_period = np.mean(diffs)
    fps = 11025
    bpm = 60 * fps / avg_period
    return float(max(60.0, min(bpm, 180.0)))
