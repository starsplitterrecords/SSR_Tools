# atf_utils.py
"""
ATF utilities

Shared helpers for parsing ATF-style filenames and grouping files
into high-level ATF buckets for UI display.

ATF filename shape (see overlay_splitter):
    "Alias - Track Name (Optional Version Name) - File Type - YYMMDD_counter.ext"
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re

# Order used in DetailsTab “ATF Types” view
ATF_GROUP_ORDER = [
    "Audio",
    "Video",
    "Image",
    "Lyrics",
    "Notes",
    "Uncategorized",
]


@dataclass(frozen=True)
class ParsedATF:
    alias: str
    track_name: str
    version_name: str
    file_type: str
    date_code: str  # YYMMDD
    counter: int
    extension: str  # lowercased, without dot


_ATF_TAIL_RE = re.compile(
    r"(?P<date>\d{6})_(?P<counter>\d{2})\.(?P<ext>[^.]+)$", re.IGNORECASE
)


def parse_atf_filename(filename: str) -> Optional[ParsedATF]:
    """
    Parse an ATF filename into components.

    Returns ParsedATF or None if the name doesn’t match the ATF shape.
    """
    if not filename:
        return None

    name = Path(filename).name  # strip any folder prefixes
    m = _ATF_TAIL_RE.search(name)
    if not m:
        return None

    date_code = m.group("date")
    try:
        counter = int(m.group("counter"))
    except ValueError:
        return None
    ext = m.group("ext").lower()

    left = name[: m.start()].rstrip(" -")
    parts = [p.strip() for p in left.split(" - ") if p.strip()]
    # Expect at least: Alias | Track/Track+Version | FileType
    if len(parts) < 3:
        return None

    alias = parts[0]
    file_type = parts[-1]
    track_section = " - ".join(parts[1:-1])

    track_name = track_section
    version_name = ""

    # Track Name (Version) pattern — use final parentheses only
    if track_section.endswith(")") and "(" in track_section:
        idx = track_section.rfind("(")
        if idx > 0 and track_section.endswith(")"):
            maybe_track = track_section[:idx].strip()
            maybe_ver = track_section[idx + 1 : -1].strip()
            if maybe_track:
                track_name = maybe_track
                version_name = maybe_ver

    return ParsedATF(
        alias=alias,
        track_name=track_name,
        version_name=version_name,
        file_type=file_type,
        date_code=date_code,
        counter=counter,
        extension=ext,
    )


# Simple extension groupings as a secondary classifier
_AUDIO_EXTS = {
    ".wav",
    ".aif",
    ".aiff",
    ".flac",
    ".mp3",
    ".m4a",
    ".ogg",
}
_VIDEO_EXTS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".m4v",
    ".webm",
}
_IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".bmp",
    ".gif",
}
_TEXT_EXTS = {
    ".txt",
    ".md",
    ".rtf",
}


def _group_from_file_type(file_type: str) -> Optional[str]:
    """
    Map a low-level ATF file_type token to a high-level group.
    Examples:
        "Audio-Master" -> "Audio"
        "Video-Short"  -> "Video"
        "Image-Promo"  -> "Image"
        "Lyrics"       -> "Lyrics"
        "Notes"        -> "Notes"
    """
    ft = (file_type or "").strip()
    if not ft:
        return None

    base = ft.split("-", 1)[0].strip().upper()
    if base == "AUDIO":
        return "Audio"
    if base == "VIDEO":
        return "Video"
    if base == "IMAGE":
        return "Image"
    if base in {"LYRICS", "LYRIC"}:
        return "Lyrics"
    if base in {"NOTES", "NOTE"}:
        return "Notes"
    return None


def _group_from_extension(filename: str) -> Optional[str]:
    """
    Fallback grouping based on file extension and basic name cues.
    """
    path = Path(filename)
    ext = path.suffix.lower()
    if not ext:
        return None

    if ext in _AUDIO_EXTS:
        return "Audio"
    if ext in _VIDEO_EXTS:
        return "Video"
    if ext in _IMAGE_EXTS:
        return "Image"
    if ext in _TEXT_EXTS:
        # Heuristic: text + “lyric” in name => Lyrics; otherwise Notes
        lower_name = path.name.lower()
        if "lyric" in lower_name:
            return "Lyrics"
        return "Notes"

    return None


def classify_atf_group(filename: str, file_type: Optional[str] = None) -> str:
    """
    Classify a file into a high-level ATF group.

    Priority:
    1) Explicit ATF file_type token (if provided)
    2) Extension-based heuristic
    3) Fallback: "Uncategorized"
    """
    # 1) Try explicit file_type
    group = _group_from_file_type(file_type or "")
    if group:
        return group

    # 2) Try extension/name
    group = _group_from_extension(filename or "")
    if group:
        return group

    # 3) Fallback
    return "Uncategorized"
