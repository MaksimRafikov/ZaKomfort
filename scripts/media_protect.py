#!/usr/bin/env python3
"""Watermark and web-optimize catalog images before publishing in assets/."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROTECTED_MARKER = "zk-protected-v1"
MAX_WEB_DIMENSION = 1440
JPEG_QUALITY = 82
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
SKIP_DIRS = {"brand"}
PHOTO_PREFIXES = ("after-", "before-", "compare-")

WATERMARK_TILE = "zakomfortom.com"
WATERMARK_BADGE = "За Комфортом"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def is_photo_filename(name: str) -> bool:
    lower = name.lower()
    return lower.startswith(PHOTO_PREFIXES)


def output_path_for(path: Path) -> Path:
    if is_photo_filename(path.name):
        return path.with_suffix(".jpg")
    return path


def is_protected_image(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            if img.info.get("zk_protected") == PROTECTED_MARKER:
                return True
            exif = img.getexif()
            if exif:
                for value in exif.values():
                    if isinstance(value, (bytes, str)) and PROTECTED_MARKER in str(value):
                        return True
    except OSError:
        return False
    return False


def _resize_for_web(img: Image.Image) -> Image.Image:
    w, h = img.size
    longest = max(w, h)
    if longest <= MAX_WEB_DIMENSION:
        return img
    scale = MAX_WEB_DIMENSION / longest
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def _draw_watermark_layer(base: Image.Image) -> Image.Image:
    rgba = base.convert("RGBA")
    overlay = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = rgba.size
    short_edge = min(width, height)

    tile_font = _font(max(18, short_edge // 28))
    badge_font = _font(max(16, short_edge // 36))

    tile_bbox = draw.textbbox((0, 0), WATERMARK_TILE, font=tile_font)
    tile_w = tile_bbox[2] - tile_bbox[0]
    tile_h = tile_bbox[3] - tile_bbox[1]
    step_x = max(tile_w + 48, width // 4)
    step_y = max(tile_h + 48, height // 4)

    tile_layer = Image.new("RGBA", (step_x, step_y), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile_layer)
    tile_draw.text((8, 8), WATERMARK_TILE, font=tile_font, fill=(255, 255, 255, 52))
    tile_rotated = tile_layer.rotate(32, expand=True, fillcolor=(0, 0, 0, 0))

    for y in range(-step_y, height + step_y, step_y):
        for x in range(-step_x, width + step_x, step_x):
            overlay.alpha_composite(tile_rotated, (x, y))

    badge_pad = max(10, short_edge // 80)
    badge_bbox = draw.textbbox((0, 0), WATERMARK_BADGE, font=badge_font)
    badge_w = badge_bbox[2] - badge_bbox[0]
    badge_h = badge_bbox[3] - badge_bbox[1]
    box_w = badge_w + badge_pad * 2
    box_h = badge_h + badge_pad * 2
    box_x = width - box_w - max(12, width // 80)
    box_y = height - box_h - max(12, height // 80)
    draw.rounded_rectangle(
        (box_x, box_y, box_x + box_w, box_y + box_h),
        radius=max(6, short_edge // 120),
        fill=(0, 0, 0, 96),
    )
    draw.text(
        (box_x + badge_pad, box_y + badge_pad - 1),
        WATERMARK_BADGE,
        font=badge_font,
        fill=(255, 255, 255, 210),
    )

    center_font = _font(max(22, short_edge // 18))
    center_text = WATERMARK_TILE
    center_bbox = draw.textbbox((0, 0), center_text, font=center_font)
    center_w = center_bbox[2] - center_bbox[0]
    center_h = center_bbox[3] - center_bbox[1]
    center_layer = Image.new("RGBA", (center_w + 24, center_h + 24), (0, 0, 0, 0))
    center_draw = ImageDraw.Draw(center_layer)
    center_draw.text((12, 12), center_text, font=center_font, fill=(255, 255, 255, 72))
    center_rotated = center_layer.rotate(-28, expand=True, fillcolor=(0, 0, 0, 0))
    overlay.alpha_composite(
        center_rotated,
        (
            max(0, (width - center_rotated.width) // 2),
            max(0, (height - center_rotated.height) // 2),
        ),
    )

    return Image.alpha_composite(rgba, overlay)


def protect_image_file(path: Path, *, force: bool = False) -> Path | None:
    """Watermark and optimize. Returns final path, or None if skipped."""
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return None

    out_path = output_path_for(path)
    if not force and out_path.exists() and is_protected_image(out_path):
        return None
    if not force and out_path == path and is_protected_image(path):
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
    watermarked = _draw_watermark_layer(img)

    if out_path.suffix.lower() == ".png":
        from PIL import PngImagePlugin

        meta = PngImagePlugin.PngInfo()
        meta.add_text("zk_protected", PROTECTED_MARKER)
        watermarked.convert("RGB").save(out_path, optimize=True, pnginfo=meta)
    else:
        exif = Image.Exif()
        exif[0x9286] = PROTECTED_MARKER.encode("utf-8")
        watermarked.convert("RGB").save(
            out_path,
            quality=JPEG_QUALITY,
            optimize=True,
            subsampling=2,
            exif=exif,
        )

    if out_path != path and path.exists():
        path.unlink()

    return out_path


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
