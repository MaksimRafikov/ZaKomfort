#!/usr/bin/env python3
"""Resize and web-optimize catalog images before publishing in assets/."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

OPTIMIZED_MARKER = "zk-optimized-v1"
LEGACY_PROTECTED_MARKER = "zk-protected-v1"
MAX_WEB_DIMENSION = 1440
JPEG_QUALITY = 82
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
SKIP_DIRS = {"brand"}
PHOTO_PREFIXES = ("after-", "before-", "compare-")


def is_photo_filename(name: str) -> bool:
    lower = name.lower()
    return lower.startswith(PHOTO_PREFIXES)


def output_path_for(path: Path) -> Path:
    if is_photo_filename(path.name):
        return path.with_suffix(".jpg")
    return path


def is_optimized_image(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            if img.info.get("zk_optimized") == OPTIMIZED_MARKER:
                return True
            if img.info.get("zk_protected") in (OPTIMIZED_MARKER, LEGACY_PROTECTED_MARKER):
                return True
            exif = img.getexif()
            if exif:
                for value in exif.values():
                    if isinstance(value, (bytes, str)) and (
                        OPTIMIZED_MARKER in str(value)
                        or LEGACY_PROTECTED_MARKER in str(value)
                    ):
                        return True
    except OSError:
        return False
    return False


# Backward-compatible alias used by validate-cases.py
is_protected_image = is_optimized_image


def _resize_for_web(img: Image.Image) -> Image.Image:
    w, h = img.size
    longest = max(w, h)
    if longest <= MAX_WEB_DIMENSION:
        return img
    scale = MAX_WEB_DIMENSION / longest
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def optimize_image_file(path: Path, *, force: bool = False) -> Path | None:
    """Resize and optimize for web. Returns final path, or None if skipped."""
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return None

    out_path = output_path_for(path)
    if not force and out_path.exists() and is_optimized_image(out_path):
        return None
    if not force and out_path == path and is_optimized_image(path):
        return None

    with Image.open(path) as opened:
        img = opened.convert("RGBA") if opened.mode in ("RGBA", "LA", "P") else opened.convert("RGB")
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert("RGB")

    img = _resize_for_web(img)

    if out_path.suffix.lower() == ".png":
        from PIL import PngImagePlugin

        meta = PngImagePlugin.PngInfo()
        meta.add_text("zk_optimized", OPTIMIZED_MARKER)
        img.save(out_path, optimize=True, pnginfo=meta)
    else:
        exif = Image.Exif()
        exif[0x9286] = OPTIMIZED_MARKER.encode("utf-8")
        img.save(
            out_path,
            quality=JPEG_QUALITY,
            optimize=True,
            subsampling=2,
            exif=exif,
        )

    if out_path != path and path.exists():
        path.unlink()

    return out_path


# Backward-compatible alias used by process-assets.py
protect_image_file = optimize_image_file


def natural_sort_key(path: Path) -> list:
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def should_skip_assets_path(path: Path, assets_root: Path) -> bool:
    try:
        rel_parts = path.relative_to(assets_root).parts
    except ValueError:
        return True
    if not rel_parts:
        return True
    if rel_parts[0] in SKIP_DIRS:
        return True
    if path.name.startswith("."):
        return True
    if path.name.lower() == "readme.md":
        return True
    return False


def iter_case_images(assets_root: Path) -> list[Path]:
    files: list[Path] = []
    if not assets_root.exists():
        return files
    for path in sorted(assets_root.rglob("*")):
        if not path.is_file():
            continue
        if should_skip_assets_path(path, assets_root):
            continue
        if path.suffix.lower() in IMAGE_SUFFIXES:
            files.append(path)
    return files
