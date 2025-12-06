# 01_core/image/engine.py
from __future__ import annotations

from PIL import Image
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, List, Tuple

from core.models import Work


ProgressCB = Optional[Callable[[str], None]]


def generate_images_for_work(
    work: Work,
    source_images: List[str],
    format_str: str,
    quality: int = 90,
    count: int = 1,
    callback: ProgressCB = None,
) -> List[str]:
    """
    Core image generation for Flet UI.

    Supports:
      - Instagram Square
      - Instagram Carousel (4:5)
      - Story (9:16)
      - Twitter Card (2:1)
      - 2x2 Grid
      - 3x3 Grid
    """

    aspect = {
        "Instagram Square": (1, 1),
        "Instagram Carousel (4:5)": (4, 5),
        "Instagram Story": (9, 16),
        "Twitter Card": (2, 1),
        "Grid 2x2": (1, 1),
        "Grid 3x3": (1, 1),
    }[format_str]

    target_size = {
        "Instagram Square": (1080, 1080),
        "Instagram Carousel (4:5)": (1080, 1350),
        "Instagram Story": (1080, 1920),
        "Twitter Card": (1600, 800),
        "Grid 2x2": (2048, 2048),
        "Grid 3x3": (3000, 3000),
    }[format_str]

    out_dir = Path(work.folder_path) / "collateral" / "graphics"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for i, path in enumerate(source_images, start=1):
        if callback:
            callback(f"Processing {path}")

        img = Image.open(path).convert("RGB")
        w, h = img.size

        aw, ah = aspect
        target_ratio = aw / ah
        img_ratio = w / h

        if img_ratio > target_ratio:
            new_w = int(h * target_ratio)
            x0 = (w - new_w) // 2
            crop = img.crop((x0, 0, x0 + new_w, h))
        else:
            new_h = int(w / target_ratio)
            y0 = (h - new_h) // 2
            crop = img.crop((0, y0, w, y0 + new_h))

        resized = crop.resize(target_size, Image.LANCZOS)

        filename = (
            f"{work.alias}-{work.uid}-{format_str.replace(' ', '_')}-"
            f"{datetime.now().strftime('%Y%m%dT%H%M%S')}_{i}.jpg"
        )
        out_path = out_dir / filename
        resized.save(out_path, "JPEG", quality=quality)

        results.append(str(out_path))

    return results
