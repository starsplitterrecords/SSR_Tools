"""
Manages video segment selection, uniqueness, and virtualization.
"""

import os
import hashlib
import random
from typing import List, Tuple, Dict

from .ffmpeg_tools import ffprobe_duration


def video_hash(path: str) -> str:
    """Hash a video by filename + size + mtime."""
    stat = os.stat(path)
    key = f"{os.path.basename(path)}_{stat.st_size}_{int(stat.st_mtime)}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


class SegmentManager:
    """Handles intelligent clip selection + anti-repetition."""

    def __init__(self, video_sources: List[str], target_beat_duration: float):
        self.video_sources = video_sources
        self.target_duration = target_beat_duration

        self.video_durations: Dict[str, float] = {}
        self.used_segments: Dict[str, List[Tuple[float, float, int]]] = {}
        self.current_slot = 0

        for v in video_sources:
            dur = ffprobe_duration(v)
            if dur:
                self.video_durations[v] = dur

    def can_fulfill_request(self, num_clips: int) -> Tuple[bool, str]:
        """Check if there's enough usable duration in the available sources."""
        if not self.video_sources:
            return False, "No video sources available"

        min_required = self.target_duration * 0.8
        longest = max(self.video_durations.values(), default=0)

        if longest < min_required:
            return False, (
                f"No video segments long enough. "
                f"Need {min_required:.1f}s, longest {longest:.1f}s"
            )

        total_available = sum(self.video_durations.values())
        needed = num_clips * self.target_duration

        if total_available < needed * 0.5:
            return True, (
                f"⚠ Limited material ({total_available:.1f}s available, "
                f"{needed:.1f}s needed) - using repetition"
            )

        return True, ""

    def get_next_segment(self) -> Tuple[str, float, float]:
        """Return (video_path, start_sec, source_duration)."""

        unique_segments = sum(len(v) for v in self.used_segments.values())
        min_span = 4 if unique_segments >= 5 else 0

        candidates = []

        for video in self.video_sources:
            video_dur = self.video_durations.get(video)
            if not video_dur:
                continue

            vh = video_hash(video)
            used = self.used_segments.get(vh, [])

            max_virtual = int(video_dur / (self.target_duration * 0.8))
            if max_virtual == 0:
                continue

            for _ in range(10):
                max_start = video_dur - (self.target_duration * 0.8)
                if max_start <= 0:
                    continue

                start = random.uniform(0, max_start)
                end = start + min(
                    self.target_duration * 1.2,
                    video_dur - start
                )

                if min_span > 0:
                    too_recent = False
                    for u_start, u_end, slot in used:
                        if self.current_slot - slot <= min_span:
                            if not (end <= u_start or start >= u_end):
                                too_recent = True
                                break
                    if too_recent:
                        continue

                source_duration = min(end - start, self.target_duration * 1.2)
                candidates.append((video, start, source_duration))
                break

        if not candidates:
            fallback = None

            for video in self.video_sources:
                vh = video_hash(video)
                used = self.used_segments.get(vh, [])
                for s, e, slot in used:
                    if fallback is None or slot < fallback[3]:
                        fallback = (video, s, min(e - s, self.target_duration * 1.2), slot)

            if fallback:
                candidates.append(fallback[:3])

        if not candidates:
            longest = max(self.video_sources, key=lambda v: self.video_durations.get(v, 0))
            dur = self.video_durations[longest]
            max_start = max(0, dur - self.target_duration * 0.8)
            start = random.uniform(0, max_start) if max_start > 0 else 0
            source_dur = min(dur - start, self.target_duration * 1.2)
            candidates.append((longest, start, source_dur))

        video, start, source_dur = random.choice(candidates)

        vh = video_hash(video)
        self.used_segments.setdefault(vh, []).append(
            (start, start + source_dur, self.current_slot)
        )
        self.current_slot += 1

        return video, start, source_dur
